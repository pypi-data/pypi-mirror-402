"""Task and setting information routes."""

from fastapi import APIRouter, HTTPException

from app.tasks_config import SETTINGS, SIDE_TASKS

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


@router.get("/settings")
async def list_settings():
    """List available Control Arena settings with metadata."""
    return SETTINGS


@router.get("/settings/{setting}/side-tasks")
async def list_side_tasks(setting: str):
    """List available side tasks for a setting."""
    if setting not in SIDE_TASKS:
        raise HTTPException(status_code=404, detail=f"Setting not found: {setting}")
    return SIDE_TASKS[setting]
