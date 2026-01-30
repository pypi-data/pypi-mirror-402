"""Export routes for downloading results and eval files."""

import csv
import io
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_admin
from app.models import Assignment, Session, User
from app.settings import get_settings

router = APIRouter(prefix="/api/v1/export", tags=["export"])
settings = get_settings()


@router.get("/sessions/{session_id}/eval-file")
async def download_eval_file(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Download the eval file for a session (admin only)."""
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    if not session.eval_log_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No eval file for this session",
        )

    file_path = Path(session.eval_log_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Eval file not found on disk",
        )

    return FileResponse(
        path=file_path,
        filename=f"session_{session_id}.eval",
        media_type="application/octet-stream",
    )


@router.get("/results.csv")
async def export_results_csv(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Export all session results as CSV (admin only)."""
    # Get all sessions with their assignments and users
    result = await db.execute(
        select(Session, Assignment, User)
        .join(Assignment, Session.assignment_id == Assignment.id)
        .join(User, Session.user_id == User.id)
        .order_by(Session.created_at.desc())
    )
    rows = result.all()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(
        [
            "session_id",
            "user_name",
            "user_email",
            "setting",
            "task_id",
            "side_task",
            "session_status",
            "main_task_score",
            "side_task_score",
            "started_at",
            "submitted_at",
            "elapsed_seconds",
            "paused_seconds",
            "has_eval_file",
        ]
    )

    # Data rows
    for session, assignment, user in rows:
        # Calculate elapsed time
        elapsed = 0
        if session.started_at and session.submitted_at:
            elapsed = int((session.submitted_at - session.started_at).total_seconds())
            elapsed = max(0, elapsed - session.paused_seconds)

        writer.writerow(
            [
                session.id,
                user.name,
                user.email,
                assignment.setting,
                assignment.task_id,
                assignment.side_task,
                session.status.value,
                session.main_task_score if session.main_task_score is not None else "",
                session.side_task_score if session.side_task_score is not None else "",
                session.started_at.isoformat() if session.started_at else "",
                session.submitted_at.isoformat() if session.submitted_at else "",
                elapsed,
                session.paused_seconds,
                "yes" if session.eval_log_path else "no",
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=human_eval_results.csv"},
    )
