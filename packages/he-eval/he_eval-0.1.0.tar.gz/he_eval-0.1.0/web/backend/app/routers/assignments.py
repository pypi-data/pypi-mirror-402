"""Assignment management routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_admin, get_current_user
from app.models import Assignment, AssignmentStatus, User
from app.schemas import (
    AssignmentCreate,
    AssignmentResponse,
    AssignmentUpdate,
    BulkAssignmentCreate,
)

router = APIRouter(prefix="/api/v1/assignments", tags=["assignments"])


@router.get("", response_model=list[AssignmentResponse])
async def list_assignments(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    all: bool = False,
):
    """List assignments.

    For regular users: returns their pending and in-progress assignments.
    For admins with all=true: returns all assignments for all users.
    """
    query = select(Assignment)

    if user.is_admin and all:
        # Admin requesting all assignments
        query = query.order_by(Assignment.assigned_at.desc())
    else:
        # Regular user or admin viewing own assignments
        query = (
            query.where(Assignment.user_id == user.id)
            .where(
                Assignment.status.in_(
                    [AssignmentStatus.PENDING, AssignmentStatus.IN_PROGRESS]
                )
            )
            .order_by(Assignment.priority.desc(), Assignment.assigned_at.asc())
        )

    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    request: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Create a new assignment (admin only)."""
    # Verify the target user exists
    user_result = await db.execute(select(User).where(User.id == request.user_id))
    if not user_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )

    assignment = Assignment(
        user_id=request.user_id,
        setting=request.setting,
        task_id=request.task_id,
        side_task=request.side_task,
        priority=request.priority,
    )
    db.add(assignment)
    await db.flush()
    await db.refresh(assignment)
    return assignment


@router.post(
    "/bulk",
    response_model=list[AssignmentResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_bulk_assignments(
    request: BulkAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Create assignments for multiple users (admin only)."""
    if not request.user_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one user ID is required",
        )

    # Verify all users exist
    result = await db.execute(select(User).where(User.id.in_(request.user_ids)))
    found_users = {u.id for u in result.scalars().all()}
    missing = set(request.user_ids) - found_users
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Users not found: {', '.join(missing)}",
        )

    # Create assignments for each user
    assignments = []
    for user_id in request.user_ids:
        assignment = Assignment(
            user_id=user_id,
            setting=request.setting,
            task_id=request.task_id,
            side_task=request.side_task,
            priority=request.priority,
        )
        db.add(assignment)
        assignments.append(assignment)

    await db.flush()
    for a in assignments:
        await db.refresh(a)

    return assignments


@router.get("/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(
    assignment_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get an assignment by ID.

    Users can only access their own assignments (admins can access all).
    """
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    # Check access
    if assignment.user_id != user.id and not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return assignment


@router.patch("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: str,
    request: AssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update an assignment.

    Users can update status of their own assignments.
    Admins can update any field.
    """
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    # Check access
    if assignment.user_id != user.id and not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Apply updates
    if request.status is not None:
        try:
            assignment.status = AssignmentStatus(request.status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {request.status}",
            )

    # Admin-only updates
    if user.is_admin:
        if request.priority is not None:
            assignment.priority = request.priority
        if request.task_id is not None:
            assignment.task_id = request.task_id
        if request.side_task is not None:
            assignment.side_task = request.side_task

    await db.flush()
    await db.refresh(assignment)
    return assignment


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(
    assignment_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Delete an assignment (admin only)."""
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    await db.delete(assignment)
