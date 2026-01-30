"""Tests for assignment endpoints."""

import pytest
from httpx import AsyncClient

from app.models import Assignment, User


@pytest.mark.asyncio
async def test_list_assignments_empty(client: AsyncClient, user_token: str):
    """Test listing assignments when none exist."""
    response = await client.get(
        "/api/v1/assignments",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_assignments(
    client: AsyncClient, user_token: str, sample_assignment: Assignment
):
    """Test listing assignments returns user's assignments."""
    response = await client.get(
        "/api/v1/assignments",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == sample_assignment.id
    assert data[0]["setting"] == "bashbench2"
    assert data[0]["task_id"] == "test_task_001"
    assert data[0]["side_task"] == "disable_firewall"
    assert data[0]["status"] == "pending"


@pytest.mark.asyncio
async def test_get_assignment(
    client: AsyncClient, user_token: str, sample_assignment: Assignment
):
    """Test getting a specific assignment."""
    response = await client.get(
        f"/api/v1/assignments/{sample_assignment.id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_assignment.id
    assert data["setting"] == "bashbench2"


@pytest.mark.asyncio
async def test_get_assignment_not_found(client: AsyncClient, user_token: str):
    """Test getting nonexistent assignment."""
    response = await client.get(
        "/api/v1/assignments/nonexistent-id",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_other_users_assignment(
    client: AsyncClient, admin_token: str, sample_assignment: Assignment
):
    """Test that admins can access other users' assignments."""
    response = await client.get(
        f"/api/v1/assignments/{sample_assignment.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_assignment_admin_only(
    client: AsyncClient,
    admin_token: str,
    regular_user: User,
):
    """Test that admins can create assignments."""
    response = await client.post(
        "/api/v1/assignments",
        json={
            "user_id": regular_user.id,
            "setting": "bashbench2",
            "task_id": "new_task",
            "side_task": "sudo_edit",
            "priority": 2,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["setting"] == "bashbench2"
    assert data["task_id"] == "new_task"
    assert data["side_task"] == "sudo_edit"
    assert data["priority"] == 2
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_create_assignment_non_admin_fails(
    client: AsyncClient,
    user_token: str,
    regular_user: User,
):
    """Test that non-admins cannot create assignments."""
    response = await client.post(
        "/api/v1/assignments",
        json={
            "user_id": regular_user.id,
            "setting": "bashbench2",
            "task_id": "new_task",
            "side_task": "sudo_edit",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_assignment_status(
    client: AsyncClient, user_token: str, sample_assignment: Assignment
):
    """Test that users can update their assignment status."""
    response = await client.patch(
        f"/api/v1/assignments/{sample_assignment.id}",
        json={"status": "in_progress"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"
