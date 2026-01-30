"""Session management routes."""

import base64
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import (
    Assignment,
    AssignmentStatus,
    Session,
    SessionEvent,
    SessionStatus,
    User,
)
from app.schemas import (
    EventCreate,
    EventResponse,
    SessionCreate,
    SessionPause,
    SessionResponse,
    SessionSubmit,
)
from app.settings import get_settings

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])
settings = get_settings()


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: SessionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new session for an assignment."""
    # Get the assignment
    result = await db.execute(
        select(Assignment).where(Assignment.id == request.assignment_id)
    )
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    # Check access
    if assignment.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your assignment",
        )

    # Check assignment status
    if assignment.status == AssignmentStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignment already completed",
        )

    # Create session
    session = Session(
        assignment_id=assignment.id,
        user_id=user.id,
    )
    db.add(session)

    # Update assignment status
    assignment.status = AssignmentStatus.IN_PROGRESS

    await db.flush()
    await db.refresh(session)
    return session


@router.get("/by-assignment/{assignment_id}", response_model=list[SessionResponse])
async def get_sessions_by_assignment(
    assignment_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get all sessions for an assignment."""
    # First verify the assignment exists and user has access
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    if assignment.user_id != user.id and not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Get all sessions for this assignment
    result = await db.execute(
        select(Session)
        .where(Session.assignment_id == assignment_id)
        .order_by(Session.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a session by ID."""
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    # Check access
    if session.user_id != user.id and not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return session


@router.patch("/{session_id}/start", response_model=SessionResponse)
async def start_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Start the timer for a session."""
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    if session.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your session",
        )

    if session.status not in [SessionStatus.CREATED, SessionStatus.PAUSED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot start session in {session.status.value} status",
        )

    session.status = SessionStatus.IN_PROGRESS
    if not session.started_at:
        session.started_at = datetime.utcnow()

    await db.flush()
    await db.refresh(session)
    return session


@router.patch("/{session_id}/pause", response_model=SessionResponse)
async def pause_session(
    session_id: str,
    request: SessionPause,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Pause a session."""
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    if session.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your session",
        )

    if session.status != SessionStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is not in progress",
        )

    session.status = SessionStatus.PAUSED

    # Log pause event
    event = SessionEvent(
        session_id=session.id,
        event_type="paused",
        event_data=json.dumps({"reason": request.reason}),
    )
    db.add(event)

    await db.flush()
    await db.refresh(session)
    return session


@router.patch("/{session_id}/resume", response_model=SessionResponse)
async def resume_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Resume a paused session."""
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    if session.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your session",
        )

    if session.status != SessionStatus.PAUSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is not paused",
        )

    session.status = SessionStatus.IN_PROGRESS

    # Log resume event
    event = SessionEvent(
        session_id=session.id,
        event_type="resumed",
    )
    db.add(event)

    await db.flush()
    await db.refresh(session)
    return session


@router.post("/{session_id}/submit", response_model=SessionResponse)
async def submit_session(
    session_id: str,
    request: SessionSubmit,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Submit session results."""
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    if session.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your session",
        )

    if session.status == SessionStatus.SUBMITTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session already submitted",
        )

    # Update session
    session.status = SessionStatus.SUBMITTED
    session.submitted_at = datetime.utcnow()
    session.main_task_score = request.main_task_score
    session.side_task_score = request.side_task_score

    # Save eval log if provided
    if request.eval_log_base64:
        # Ensure directory exists
        settings.eval_logs_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        log_path = settings.eval_logs_dir / f"{session.id}.eval"
        log_data = base64.b64decode(request.eval_log_base64)
        log_path.write_bytes(log_data)
        session.eval_log_path = str(log_path)

    # Update assignment status
    assignment_result = await db.execute(
        select(Assignment).where(Assignment.id == session.assignment_id)
    )
    assignment = assignment_result.scalar_one_or_none()
    if assignment:
        assignment.status = AssignmentStatus.COMPLETED

    # Log submit event
    event = SessionEvent(
        session_id=session.id,
        event_type="submitted",
        event_data=json.dumps(
            {
                "main_task_score": request.main_task_score,
                "side_task_score": request.side_task_score,
            }
        ),
    )
    db.add(event)

    await db.flush()
    await db.refresh(session)
    return session


# --- Event endpoints ---


@router.post("/{session_id}/events", status_code=status.HTTP_201_CREATED)
async def log_event(
    session_id: str,
    request: EventCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Log an event for a session."""
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    if session.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your session",
        )

    event = SessionEvent(
        session_id=session.id,
        event_type=request.event_type,
        event_data=json.dumps(request.event_data) if request.event_data else None,
        client_timestamp=request.client_timestamp,
    )
    db.add(event)
    await db.flush()

    return {"status": "ok"}


@router.get("/{session_id}/events", response_model=list[EventResponse])
async def get_events(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get events for a session."""
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    # Check access
    if session.user_id != user.id and not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    events_result = await db.execute(
        select(SessionEvent)
        .where(SessionEvent.session_id == session_id)
        .order_by(SessionEvent.server_timestamp.asc())
    )
    return events_result.scalars().all()
