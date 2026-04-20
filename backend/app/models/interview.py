from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

from app.common.enums import (
    InterviewMode,
    InterviewStatus,
    InterviewerType,
    SpeakerType,
    TurnKind,
)
from app.models.base import BaseModel


class InterviewSession(BaseModel, table=True):
    __tablename__ = "interview_sessions"
    __table_args__ = (
        Index("ix_interview_sessions_user_id", "user_id"),
        Index("ix_interview_sessions_status", "status"),
        Index("ix_interview_sessions_created_at_desc", text("created_at DESC")),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(
        sa_column=Column(
            Uuid(as_uuid=True),
            ForeignKey("user.id"),
            nullable=False,
        ),
    )
    resume_id: UUID = Field(
        sa_column=Column(
            Uuid(as_uuid=True),
            ForeignKey("resumes.id"),
            nullable=False,
        ),
    )
    job_description_id: UUID = Field(
        sa_column=Column(
            Uuid(as_uuid=True),
            ForeignKey("job_descriptions.id"),
            nullable=False,
        ),
    )
    status: InterviewStatus = Field(
        default=InterviewStatus.draft,
        sa_column=Column(
            SAEnum(InterviewStatus, name="interview_status", native_enum=True),
            nullable=False,
            server_default=text("'draft'::interview_status"),
        ),
    )
    interview_type: str = Field(sa_column=Column(String(255), nullable=False))
    title: Optional[str] = Field(
        default=None,
        sa_column=Column(String(512), nullable=True),
    )
    interview_context_json: Optional[dict[str, Any]] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    )
    question_count: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False, server_default=text("0")),
    )
    duration_seconds: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, nullable=True),
    )
    started_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )


class InterviewTurn(BaseModel, table=True):
    __tablename__ = "interview_turns"
    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "sequence_no",
            name="uq_interview_turns_session_sequence",
        ),
        Index("ix_interview_turns_session_id", "session_id"),
        Index("ix_interview_turns_speaker_type", "speaker_type"),
        Index("ix_interview_turns_created_at", "created_at"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(
        sa_column=Column(
            Uuid(as_uuid=True),
            ForeignKey("interview_sessions.id"),
            nullable=False,
        ),
    )
    participant_id: Optional[UUID] = Field(
        default=None,
        sa_column=Column(
            Uuid(as_uuid=True),
            ForeignKey("session_participants.id"),
            nullable=True,
        ),
    )
    speaker_type: SpeakerType = Field(
        sa_column=Column(
            SAEnum(SpeakerType, name="speaker_type", native_enum=True),
            nullable=False,
        ),
    )
    turn_kind: TurnKind = Field(
        sa_column=Column(
            SAEnum(TurnKind, name="turn_kind", native_enum=True),
            nullable=False,
        ),
    )
    sequence_no: int = Field(sa_column=Column(Integer, nullable=False))
    content_text: str = Field(sa_column=Column(Text, nullable=False))
    is_final: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, server_default=text("true")),
    )
    latency_ms: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, nullable=True),
    )
    metadata_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    )
