"""Tests for session lifecycle endpoints."""

import pytest
from httpx import AsyncClient

from app.models import Assignment, User


@pytest.mark.asyncio
async def test_session_lifecycle(
    client: AsyncClient, user_token: str, sample_assignment: Assignment
):
    """Test the full session lifecycle: create -> start -> pause -> resume -> submit."""
    # 1. Create session
    response = await client.post(
        "/api/v1/sessions",
        json={"assignment_id": sample_assignment.id},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 201
    session = response.json()
    session_id = session["id"]
    assert session["status"] == "created"
    assert session["assignment_id"] == sample_assignment.id
    assert session["started_at"] is None

    # 2. Start session
    response = await client.patch(
        f"/api/v1/sessions/{session_id}/start",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    session = response.json()
    assert session["status"] == "in_progress"
    assert session["started_at"] is not None

    # 3. Pause session
    response = await client.patch(
        f"/api/v1/sessions/{session_id}/pause",
        json={"reason": "taking a break"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    session = response.json()
    assert session["status"] == "paused"

    # 4. Resume session
    response = await client.patch(
        f"/api/v1/sessions/{session_id}/resume",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    session = response.json()
    assert session["status"] == "in_progress"

    # 5. Submit session
    response = await client.post(
        f"/api/v1/sessions/{session_id}/submit",
        json={
            "main_task_score": 0.75,
            "side_task_score": 1.0,
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    session = response.json()
    assert session["status"] == "submitted"
    assert session["main_task_score"] == 0.75
    assert session["side_task_score"] == 1.0
    assert session["submitted_at"] is not None


@pytest.mark.asyncio
async def test_create_session_updates_assignment(
    client: AsyncClient, user_token: str, sample_assignment: Assignment
):
    """Test that creating a session updates assignment status."""
    # Create session
    await client.post(
        "/api/v1/sessions",
        json={"assignment_id": sample_assignment.id},
        headers={"Authorization": f"Bearer {user_token}"},
    )

    # Check assignment status
    response = await client.get(
        f"/api/v1/assignments/{sample_assignment.id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.json()["status"] == "in_progress"


@pytest.mark.asyncio
async def test_submit_session_completes_assignment(
    client: AsyncClient, user_token: str, sample_assignment: Assignment
):
    """Test that submitting a session marks assignment as completed."""
    # Create and start session
    response = await client.post(
        "/api/v1/sessions",
        json={"assignment_id": sample_assignment.id},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    session_id = response.json()["id"]

    await client.patch(
        f"/api/v1/sessions/{session_id}/start",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    # Submit
    await client.post(
        f"/api/v1/sessions/{session_id}/submit",
        json={"main_task_score": 1.0, "side_task_score": 0.0},
        headers={"Authorization": f"Bearer {user_token}"},
    )

    # Check assignment status
    response = await client.get(
        f"/api/v1/assignments/{sample_assignment.id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_cannot_start_submitted_session(
    client: AsyncClient, user_token: str, sample_assignment: Assignment
):
    """Test that submitted sessions cannot be restarted."""
    # Create, start, submit
    response = await client.post(
        "/api/v1/sessions",
        json={"assignment_id": sample_assignment.id},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    session_id = response.json()["id"]

    await client.patch(
        f"/api/v1/sessions/{session_id}/start",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    await client.post(
        f"/api/v1/sessions/{session_id}/submit",
        json={"main_task_score": 1.0, "side_task_score": 0.0},
        headers={"Authorization": f"Bearer {user_token}"},
    )

    # Try to start again
    response = await client.patch(
        f"/api/v1/sessions/{session_id}/start",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_cannot_pause_non_running_session(
    client: AsyncClient, user_token: str, sample_assignment: Assignment
):
    """Test that only in-progress sessions can be paused."""
    # Create session but don't start it
    response = await client.post(
        "/api/v1/sessions",
        json={"assignment_id": sample_assignment.id},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    session_id = response.json()["id"]

    # Try to pause without starting
    response = await client.patch(
        f"/api/v1/sessions/{session_id}/pause",
        json={"reason": "test"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_log_event(
    client: AsyncClient, user_token: str, sample_assignment: Assignment
):
    """Test logging events to a session."""
    # Create session
    response = await client.post(
        "/api/v1/sessions",
        json={"assignment_id": sample_assignment.id},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    session_id = response.json()["id"]

    # Log event
    response = await client.post(
        f"/api/v1/sessions/{session_id}/events",
        json={
            "event_type": "docker_started",
            "event_data": {"container_id": "abc123"},
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 201

    # Get events
    response = await client.get(
        f"/api/v1/sessions/{session_id}/events",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    events = response.json()
    assert len(events) == 1
    assert events[0]["event_type"] == "docker_started"


@pytest.mark.asyncio
async def test_cannot_access_other_users_session(
    client: AsyncClient,
    admin_token: str,
    user_token: str,
    sample_assignment: Assignment,
    admin_user: User,
):
    """Test that users cannot access other users' sessions (except admins)."""
    # Create session as regular user
    response = await client.post(
        "/api/v1/sessions",
        json={"assignment_id": sample_assignment.id},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    session_id = response.json()["id"]

    # Admin can access
    response = await client.get(
        f"/api/v1/sessions/{session_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200

    # But cannot start it (not their session)
    response = await client.patch(
        f"/api/v1/sessions/{session_id}/start",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 403
