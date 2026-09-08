from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    settings_json: Mapped[dict[str, object]] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ScoringConfiguration(Base):
    __tablename__ = "scoring_configurations"
    __table_args__ = (
        UniqueConstraint("organization_id", "version_no", name="uq_scoring_configuration_version"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    version_no: Mapped[int] = mapped_column(Integer)
    weights_json: Mapped[dict[str, object]] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb")
    )
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    auth_subject: Mapped[str] = mapped_column(String(255), unique=True)
    email: Mapped[str] = mapped_column(String(320))
    display_name: Mapped[str] = mapped_column(String(200))
    password_hash: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    organization_id: Mapped[UUID | None] = mapped_column(ForeignKey("organizations.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    organization_id: Mapped[UUID | None] = mapped_column(ForeignKey("organizations.id"), index=True)
    actor_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(64), index=True)
    entity_type: Mapped[str | None] = mapped_column(String(64))
    entity_id: Mapped[str | None] = mapped_column(String(64))
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_membership_org_user"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(32))


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        Index("ix_projects_organization_department", "organization_id", "department"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    department: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(16), server_default=text("'active'"))
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Process(Base):
    __tablename__ = "processes"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(16), server_default=text("'active'"))
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProcessVersion(Base):
    __tablename__ = "process_versions"
    __table_args__ = (UniqueConstraint("process_id", "version_no", name="uq_process_version_no"),)
    id: Mapped[UUID] = mapped_column(primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    process_id: Mapped[UUID] = mapped_column(ForeignKey("processes.id"), index=True)
    version_no: Mapped[int] = mapped_column(Integer)
    review_status: Mapped[str] = mapped_column(String(16), server_default=text("'draft'"))
    source_summary: Mapped[str] = mapped_column(Text)
    metrics_json: Mapped[dict[str, object]] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb")
    )
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProcessVersionComment(Base):
    __tablename__ = "process_version_comments"
    __table_args__ = (
        Index(
            "ix_process_version_comments_organization_version_created",
            "organization_id",
            "process_version_id",
            "created_at",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    process_version_id: Mapped[UUID] = mapped_column(ForeignKey("process_versions.id"), index=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"
    __table_args__ = (
        UniqueConstraint("organization_id", "idempotency_key", name="uq_analysis_idempotency"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    process_version_id: Mapped[UUID] = mapped_column(ForeignKey("process_versions.id"))
    status: Mapped[str] = mapped_column(String(16), server_default=text("'queued'"), index=True)
    task: Mapped[str] = mapped_column(String(32), server_default=text("'process_extraction'"))
    provider: Mapped[str | None] = mapped_column(String(32))
    model_id: Mapped[str | None] = mapped_column(String(120))
    prompt_version: Mapped[str | None] = mapped_column(String(64))
    schema_version: Mapped[str | None] = mapped_column(String(64))
    scoring_version: Mapped[str | None] = mapped_column(String(64))
    scoring_configuration_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("scoring_configurations.id"), index=True
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(64))
    error_code: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Actor(Base):
    __tablename__ = "actors"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    process_version_id: Mapped[UUID] = mapped_column(ForeignKey("process_versions.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    type: Mapped[str | None] = mapped_column(String(64))


class Evidence(Base):
    __tablename__ = "evidences"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    process_version_id: Mapped[UUID] = mapped_column(ForeignKey("process_versions.id"), index=True)
    source_type: Mapped[str] = mapped_column(String(32))
    source_ref: Mapped[str | None] = mapped_column(String(64))
    excerpt: Mapped[str] = mapped_column(Text)
    reviewed: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    confidence: Mapped[str | None] = mapped_column(String(8))


class ProcessDocument(Base):
    __tablename__ = "process_documents"
    __table_args__ = (
        Index(
            "ix_process_documents_organization_process_created",
            "organization_id",
            "process_id",
            "created_at",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    process_id: Mapped[UUID] = mapped_column(ForeignKey("processes.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    media_type: Mapped[str] = mapped_column(String(64))
    byte_size: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    extracted_text: Mapped[str] = mapped_column(Text)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class System(Base):
    __tablename__ = "systems"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    process_version_id: Mapped[UUID] = mapped_column(ForeignKey("process_versions.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    integration_status: Mapped[str] = mapped_column(String(32), server_default=text("'unknown'"))
    integration_evidence_id: Mapped[UUID | None] = mapped_column(ForeignKey("evidences.id"))


class ProcessStep(Base):
    __tablename__ = "process_steps"
    __table_args__ = (
        UniqueConstraint("process_version_id", "step_key", name="uq_step_key_per_version"),
        Index("ix_process_steps_version", "process_version_id", "sequence_no"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    process_version_id: Mapped[UUID] = mapped_column(ForeignKey("process_versions.id"))
    step_key: Mapped[str] = mapped_column(String(16))
    sequence_no: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(300))
    actor_id: Mapped[UUID | None] = mapped_column(ForeignKey("actors.id"))
    system_id: Mapped[UUID | None] = mapped_column(ForeignKey("systems.id"))
    manual: Mapped[bool | None] = mapped_column()
    duration_minutes: Mapped[float | None] = mapped_column(Float)
    data_json: Mapped[dict[str, object]] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))


class PainPoint(Base):
    __tablename__ = "pain_points"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    analysis_run_id: Mapped[UUID] = mapped_column(ForeignKey("analysis_runs.id"), index=True)
    category: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(8))
    confidence: Mapped[str] = mapped_column(String(8))
    evidence_json: Mapped[list[object]] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))


class Opportunity(Base):
    __tablename__ = "opportunities"
    __table_args__ = (
        Index("ix_opportunities_organization_analysis", "organization_id", "analysis_run_id"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    analysis_run_id: Mapped[UUID] = mapped_column(ForeignKey("analysis_runs.id"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    scope_json: Mapped[dict[str, object]] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    confidence: Mapped[int] = mapped_column()
    status: Mapped[str] = mapped_column(String(16), server_default=text("'candidate'"))
    result_state: Mapped[str] = mapped_column(
        String(24), server_default=text("'insufficient_evidence'")
    )


class OpportunityScore(Base):
    __tablename__ = "opportunity_scores"
    __table_args__ = (
        Index(
            "ix_opportunity_scores_organization_opportunity_created",
            "organization_id",
            "opportunity_id",
            "created_at",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    opportunity_id: Mapped[UUID] = mapped_column(ForeignKey("opportunities.id"), index=True)
    total_score: Mapped[float | None] = mapped_column(Float)
    dimension_json: Mapped[dict[str, object]] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb")
    )
    confidence_score: Mapped[int] = mapped_column()
    scoring_version: Mapped[str] = mapped_column(String(64))
    scoring_configuration_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("scoring_configurations.id"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Recommendation(Base):
    __tablename__ = "recommendations"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    opportunity_id: Mapped[UUID] = mapped_column(ForeignKey("opportunities.id"), index=True)
    patterns_json: Mapped[list[object]] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    rationale: Mapped[str] = mapped_column(Text)
    prerequisites_json: Mapped[list[object]] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb")
    )
    risks_json: Mapped[list[object]] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    human_control: Mapped[str] = mapped_column(Text)
    rejected_alternatives_json: Mapped[list[object]] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb")
    )
    confidence: Mapped[str] = mapped_column(String(8))


class RoiScenario(Base):
    __tablename__ = "roi_scenarios"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    opportunity_id: Mapped[UUID] = mapped_column(ForeignKey("opportunities.id"), index=True)
    input_json: Mapped[dict[str, object]] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    output_json: Mapped[dict[str, object]] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Report(Base):
    __tablename__ = "reports"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    analysis_run_id: Mapped[UUID] = mapped_column(ForeignKey("analysis_runs.id"), index=True)
    status: Mapped[str] = mapped_column(String(16), server_default=text("'ready'"))
    snapshot_json: Mapped[dict[str, object]] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb")
    )
    storage_key: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
