"""SQLAlchemy ORM models for the human evaluation system."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())


class AssignmentStatus(enum.Enum):
    """Status of a task assignment."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SessionStatus(enum.Enum):
    """Status of a work session."""

    CREATED = "created"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    SUBMITTED = "submitted"
    CANCELLED = "cancelled"


class User(Base):
    """A user who can complete evaluations."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_admin: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    api_keys: Mapped[list["ApiKey"]] = relationship(back_populates="user")
    assignments: Mapped[list["Assignment"]] = relationship(back_populates="user")
    sessions: Mapped[list["Session"]] = relationship(back_populates="user")


class ApiKey(Base):
    """API key for CLI authentication."""

    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="api_keys")


class Assignment(Base):
    """A task assigned to a user."""

    __tablename__ = "assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )

    # Task specification
    setting: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # e.g., "bashbench2"
    task_id: Mapped[str] = mapped_column(String(255), nullable=False)
    side_task: Mapped[str] = mapped_column(String(255), nullable=False)

    # Status tracking
    status: Mapped[AssignmentStatus] = mapped_column(
        Enum(AssignmentStatus), default=AssignmentStatus.PENDING, nullable=False
    )
    priority: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="assignments")
    sessions: Mapped[list["Session"]] = relationship(back_populates="assignment")


class Session(Base):
    """A work session for completing an assignment."""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    assignment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assignments.id"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )

    # Status
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus), default=SessionStatus.CREATED, nullable=False
    )

    # Timing
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    paused_seconds: Mapped[int] = mapped_column(Integer, default=0)

    # Results
    main_task_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    side_task_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    eval_log_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    assignment: Mapped["Assignment"] = relationship(back_populates="sessions")
    user: Mapped["User"] = relationship(back_populates="sessions")
    events: Mapped[list["SessionEvent"]] = relationship(back_populates="session")

    @property
    def elapsed_seconds(self) -> int | None:
        """Calculate elapsed time in seconds, excluding paused time."""
        if not self.started_at:
            return None

        end_time = self.submitted_at or datetime.utcnow()
        total_seconds = int((end_time - self.started_at).total_seconds())
        return max(0, total_seconds - self.paused_seconds)


class SessionEvent(Base):
    """An event that occurred during a session."""

    __tablename__ = "session_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id"), nullable=False
    )

    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string

    # Timestamps
    client_timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    server_timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    session: Mapped["Session"] = relationship(back_populates="events")
