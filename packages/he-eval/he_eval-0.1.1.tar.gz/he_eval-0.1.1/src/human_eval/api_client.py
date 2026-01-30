"""HTTP API client for communicating with the human-eval backend.

Provides typed methods for all API endpoints with retry logic
and proper error handling.
"""

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

from human_eval.config import load_config

# Retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 1.0  # seconds
RETRY_STATUS_CODES = {500, 502, 503, 504}


class APIError(Exception):
    """Base exception for API errors."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class AuthenticationError(APIError):
    """Raised when authentication fails."""

    pass


class NotFoundError(APIError):
    """Raised when a resource is not found."""

    pass


@dataclass
class Assignment:
    """Task assignment from the backend."""

    id: str
    setting: str
    task_id: str
    side_task: str
    status: str
    priority: int


@dataclass
class Session:
    """Work session for an assignment."""

    id: str
    assignment_id: str
    status: str
    started_at: datetime | None
    submitted_at: datetime | None
    main_task_score: float | None
    side_task_score: float | None


@dataclass
class TokenResponse:
    """Response from token exchange."""

    api_key: str
    expires_at: datetime
    user_email: str
    user_name: str


class APIClient:
    """HTTP client for the human-eval backend API."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        """Initialize the API client.

        Args:
            base_url: Backend URL. If None, loads from config.
            api_key: API key for auth. If None, loads from config.
        """
        config = load_config()
        self.base_url = (base_url or config.server.url).rstrip("/")
        self.api_key = api_key or config.auth.api_key

        if not self.base_url:
            raise APIError("No server URL configured. Run 'he-cli auth login' first.")

    def _headers(self) -> dict[str, str]:
        """Build request headers with authentication."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        require_auth: bool = True,
    ) -> dict[str, Any]:
        """Make an HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            path: API path (e.g., "/api/v1/assignments")
            json: Request body as dict
            params: Query parameters
            require_auth: Whether to require authentication

        Returns:
            Response JSON as dict

        Raises:
            APIError: On request failure
            AuthenticationError: On 401/403
            NotFoundError: On 404
        """
        if require_auth and not self.api_key:
            raise AuthenticationError(
                "Not authenticated. Run 'he-cli auth login' first."
            )

        url = f"{self.base_url}{path}"
        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                with httpx.Client(timeout=30.0) as client:
                    response = client.request(
                        method=method,
                        url=url,
                        json=json,
                        params=params,
                        headers=self._headers(),
                    )

                # Handle specific status codes
                if response.status_code == 401:
                    raise AuthenticationError("Invalid or expired API key", 401)
                if response.status_code == 403:
                    raise AuthenticationError("Access denied", 403)
                if response.status_code == 404:
                    raise NotFoundError(f"Resource not found: {path}", 404)

                # Retry on server errors
                if response.status_code in RETRY_STATUS_CODES:
                    last_error = APIError(
                        f"Server error: {response.status_code}", response.status_code
                    )
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_BACKOFF_BASE * (2**attempt))
                        continue
                    raise last_error

                # Raise on other errors
                if response.status_code >= 400:
                    try:
                        detail = response.json().get("detail", response.text)
                    except Exception:
                        detail = response.text
                    raise APIError(f"Request failed: {detail}", response.status_code)

                # Success - return JSON or empty dict
                if response.status_code == 204:
                    return {}
                return response.json()

            except httpx.RequestError as e:
                last_error = APIError(f"Connection error: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF_BASE * (2**attempt))
                    continue
                raise last_error from e

        raise last_error or APIError("Request failed after retries")

    # --- Auth endpoints ---

    def exchange_code_for_token(self, code: str) -> TokenResponse:
        """Exchange a one-time code for an API key.

        Args:
            code: One-time code from web UI

        Returns:
            TokenResponse with API key and user info
        """
        data = self._request(
            "POST",
            "/api/v1/auth/token",
            json={"code": code},
            require_auth=False,
        )
        return TokenResponse(
            api_key=data["api_key"],
            expires_at=datetime.fromisoformat(data["expires_at"]),
            user_email=data["user_email"],
            user_name=data["user_name"],
        )

    # --- Assignment endpoints ---

    def list_assignments(self) -> list[Assignment]:
        """List pending assignments for the current user."""
        data = self._request("GET", "/api/v1/assignments")
        return [
            Assignment(
                id=a["id"],
                setting=a["setting"],
                task_id=a["task_id"],
                side_task=a["side_task"],
                status=a["status"],
                priority=a["priority"],
            )
            for a in data
        ]

    def get_assignment(self, assignment_id: str) -> Assignment:
        """Get a specific assignment by ID."""
        data = self._request("GET", f"/api/v1/assignments/{assignment_id}")
        return Assignment(
            id=data["id"],
            setting=data["setting"],
            task_id=data["task_id"],
            side_task=data["side_task"],
            status=data["status"],
            priority=data["priority"],
        )

    # --- Session endpoints ---

    def create_session(self, assignment_id: str) -> Session:
        """Create a new session for an assignment."""
        data = self._request(
            "POST",
            "/api/v1/sessions",
            json={"assignment_id": assignment_id},
        )
        return self._parse_session(data)

    def get_session(self, session_id: str) -> Session:
        """Get a session by ID."""
        data = self._request("GET", f"/api/v1/sessions/{session_id}")
        return self._parse_session(data)

    def start_session(self, session_id: str) -> Session:
        """Start the timer for a session."""
        data = self._request("PATCH", f"/api/v1/sessions/{session_id}/start")
        return self._parse_session(data)

    def pause_session(self, session_id: str, reason: str = "") -> Session:
        """Pause a session."""
        data = self._request(
            "PATCH",
            f"/api/v1/sessions/{session_id}/pause",
            json={"reason": reason},
        )
        return self._parse_session(data)

    def resume_session(self, session_id: str) -> Session:
        """Resume a paused session."""
        data = self._request("PATCH", f"/api/v1/sessions/{session_id}/resume")
        return self._parse_session(data)

    def submit_session(
        self,
        session_id: str,
        main_task_score: float,
        side_task_score: float,
        eval_log_path: str | None = None,
    ) -> Session:
        """Submit session results.

        Args:
            session_id: Session to submit
            main_task_score: Main task score (0.0-1.0)
            side_task_score: Side task score (0.0-1.0)
            eval_log_path: Optional path to .eval file to upload
        """
        payload: dict[str, Any] = {
            "main_task_score": main_task_score,
            "side_task_score": side_task_score,
        }

        # Read and include eval log if provided
        if eval_log_path:
            import base64
            from pathlib import Path

            eval_path = Path(eval_log_path)
            if eval_path.exists():
                payload["eval_log_base64"] = base64.b64encode(
                    eval_path.read_bytes()
                ).decode("utf-8")

        data = self._request(
            "POST",
            f"/api/v1/sessions/{session_id}/submit",
            json=payload,
        )
        return self._parse_session(data)

    def _parse_session(self, data: dict[str, Any]) -> Session:
        """Parse session data from API response."""
        return Session(
            id=data["id"],
            assignment_id=data["assignment_id"],
            status=data["status"],
            started_at=(
                datetime.fromisoformat(data["started_at"])
                if data.get("started_at")
                else None
            ),
            submitted_at=(
                datetime.fromisoformat(data["submitted_at"])
                if data.get("submitted_at")
                else None
            ),
            main_task_score=data.get("main_task_score"),
            side_task_score=data.get("side_task_score"),
        )

    # --- Event endpoints ---

    def log_event(
        self,
        session_id: str,
        event_type: str,
        event_data: dict[str, Any] | None = None,
    ) -> None:
        """Log an event for a session.

        Args:
            session_id: Session the event belongs to
            event_type: Type of event (e.g., "docker_started", "command_executed")
            event_data: Optional additional data for the event
        """
        self._request(
            "POST",
            f"/api/v1/sessions/{session_id}/events",
            json={
                "event_type": event_type,
                "event_data": event_data or {},
                "client_timestamp": datetime.now().isoformat(),
            },
        )
