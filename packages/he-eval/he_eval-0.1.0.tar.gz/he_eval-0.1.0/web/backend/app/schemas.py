"""Pydantic schemas for API request/response validation."""

from datetime import datetime

from pydantic import BaseModel, EmailStr


# --- Auth schemas ---


class TokenRequest(BaseModel):
    """Request to exchange a code for an API key."""

    code: str


class TokenResponse(BaseModel):
    """Response with API key and user info."""

    api_key: str
    expires_at: datetime
    user_email: str
    user_name: str


class LoginRequest(BaseModel):
    """Web login request."""

    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Web login response with JWT."""

    access_token: str
    token_type: str = "bearer"


# --- User schemas ---


class UserCreate(BaseModel):
    """Create a new user."""

    email: EmailStr
    name: str
    password: str
    is_admin: bool = False


class UserResponse(BaseModel):
    """User information response."""

    id: str
    email: str
    name: str
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    """Change own password."""

    current_password: str
    new_password: str


class PasswordReset(BaseModel):
    """Admin reset user password."""

    new_password: str


# --- Assignment schemas ---


class AssignmentCreate(BaseModel):
    """Create a new assignment."""

    user_id: str
    setting: str
    task_id: str
    side_task: str
    priority: int = 0


class AssignmentResponse(BaseModel):
    """Assignment information response."""

    id: str
    user_id: str
    setting: str
    task_id: str
    side_task: str
    status: str
    priority: int
    assigned_at: datetime

    class Config:
        from_attributes = True


class AssignmentUpdate(BaseModel):
    """Update an assignment."""

    status: str | None = None
    priority: int | None = None
    task_id: str | None = None
    side_task: str | None = None


class BulkAssignmentCreate(BaseModel):
    """Create assignments for multiple users."""

    user_ids: list[str]
    setting: str
    task_id: str
    side_task: str
    priority: int = 0


# --- Session schemas ---


class SessionCreate(BaseModel):
    """Create a new session."""

    assignment_id: str


class SessionResponse(BaseModel):
    """Session information response."""

    id: str
    assignment_id: str
    user_id: str
    status: str
    created_at: datetime
    started_at: datetime | None = None
    submitted_at: datetime | None = None
    paused_seconds: int = 0
    main_task_score: float | None = None
    side_task_score: float | None = None
    eval_log_path: str | None = None

    class Config:
        from_attributes = True


class SessionPause(BaseModel):
    """Pause a session."""

    reason: str = ""


class SessionSubmit(BaseModel):
    """Submit session results."""

    main_task_score: float
    side_task_score: float
    eval_log_base64: str | None = None  # Base64-encoded .eval file


# --- Event schemas ---


class EventCreate(BaseModel):
    """Log an event."""

    event_type: str
    event_data: dict | None = None
    client_timestamp: datetime | None = None


class EventResponse(BaseModel):
    """Event information response."""

    id: str
    session_id: str
    event_type: str
    event_data: str | None = None
    client_timestamp: datetime | None = None
    server_timestamp: datetime

    class Config:
        from_attributes = True
