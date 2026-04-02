from decimal import Decimal
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    Uuid,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

from app.common.enums import FileKind, ParseStatus
from app.models.base import BaseModel


class File(BaseModel, table=True):
    __tablename__ = "files"
    __table_args__ = (
        Index("ix_files_user_id", "user_id"),
        Index("ix_files_kind", "kind"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", nullable=False)
    kind: FileKind = Field(
        sa_column=Column(
            SAEnum(FileKind, name="file_kind", native_enum=True), nullable=False
        ),
    )
    storage_key: str = Field(sa_column=Column(String(2048), nullable=False))
    original_filename: Optional[str] = Field(
        default=None, sa_column=Column(String(512), nullable=True)
    )
    mime_type: Optional[str] = Field(
        default=None, sa_column=Column(String(255), nullable=True)
    )
    size_bytes: Optional[int] = Field(
        default=None, sa_column=Column(BigInteger, nullable=True)
    )
    checksum: Optional[str] = Field(
        default=None, sa_column=Column(String(128), nullable=True)
    )


class Resume(BaseModel, table=True):
    __tablename__ = "resumes"
    __table_args__ = (
        Index("ix_resumes_user_id", "user_id"),
        Index("ix_resumes_parse_status", "parse_status"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", nullable=False)
    file_id: UUID = Field(foreign_key="files.id", nullable=False)
    title: Optional[str] = Field(
        default=None, sa_column=Column(String(512), nullable=True)
    )
    version_label: Optional[str] = Field(
        default=None, sa_column=Column(String(255), nullable=True)
    )
    parse_status: ParseStatus = Field(
        default=ParseStatus.pending,
        sa_column=Column(
            SAEnum(ParseStatus, name="parse_status", native_enum=True),
            nullable=False,
            server_default=text("'pending'::parse_status"),
        ),
    )
    is_default: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, server_default=text("false")),
    )


class ParsedResume(BaseModel, table=True):
    """Normalized parsed resume output (one row per resume)."""

    __tablename__ = "parsed_resumes"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    resume_id: UUID = Field(
        sa_column=Column(
            Uuid(as_uuid=True),
            ForeignKey("resumes.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
    )
    full_text: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    candidate_summary: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    total_years_experience: Optional[Decimal] = Field(
        default=None, sa_column=Column(Numeric(4, 1), nullable=True)
    )
    skills_json: list[Any] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False, server_default=text("'[]'::jsonb")),
    )
    experience_json: list[Any] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False, server_default=text("'[]'::jsonb")),
    )
    projects_json: list[Any] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False, server_default=text("'[]'::jsonb")),
    )
    education_json: list[Any] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False, server_default=text("'[]'::jsonb")),
    )
    certifications_json: list[Any] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False, server_default=text("'[]'::jsonb")),
    )
    parse_metadata_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    )


class JobDescription(BaseModel, table=True):
    __tablename__ = "job_descriptions"
    __table_args__ = (
        Index("ix_job_descriptions_user_id", "user_id"),
        Index("ix_job_descriptions_company_name", "company_name"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", nullable=False)
    title: Optional[str] = Field(
        default=None, sa_column=Column(String(512), nullable=True)
    )
    company_name: Optional[str] = Field(
        default=None, sa_column=Column(String(255), nullable=True)
    )
    raw_text: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
