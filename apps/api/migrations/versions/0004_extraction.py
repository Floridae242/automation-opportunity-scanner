"""M3 extraction: analysis runs, steps, actors, systems, evidence."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004_extraction"
down_revision = "0003_intake"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "analysis_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column(
            "process_version_id", sa.Uuid(), sa.ForeignKey("process_versions.id"), nullable=False
        ),
        sa.Column("status", sa.String(16), nullable=False, server_default="queued"),
        sa.Column("task", sa.String(32), nullable=False, server_default="process_extraction"),
        sa.Column("provider", sa.String(32), nullable=True),
        sa.Column("model_id", sa.String(120), nullable=True),
        sa.Column("prompt_version", sa.String(64), nullable=True),
        sa.Column("schema_version", sa.String(64), nullable=True),
        sa.Column("scoring_version", sa.String(64), nullable=True),
        sa.Column("idempotency_key", sa.String(64), nullable=True),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_analysis_runs_organization_id", "analysis_runs", ["organization_id"])
    op.create_index("ix_analysis_runs_status", "analysis_runs", ["status"])
    op.create_unique_constraint(
        "uq_analysis_idempotency", "analysis_runs", ["organization_id", "idempotency_key"]
    )
    op.create_table(
        "actors",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column(
            "process_version_id", sa.Uuid(), sa.ForeignKey("process_versions.id"), nullable=False
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("type", sa.String(64), nullable=True),
    )
    op.create_index("ix_actors_organization_id", "actors", ["organization_id"])
    op.create_index("ix_actors_process_version_id", "actors", ["process_version_id"])
    op.create_table(
        "evidences",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column(
            "process_version_id", sa.Uuid(), sa.ForeignKey("process_versions.id"), nullable=False
        ),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("source_ref", sa.String(64), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("reviewed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("confidence", sa.String(8), nullable=True),
    )
    op.create_index("ix_evidences_organization_id", "evidences", ["organization_id"])
    op.create_index("ix_evidences_process_version_id", "evidences", ["process_version_id"])
    op.create_table(
        "systems",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column(
            "process_version_id", sa.Uuid(), sa.ForeignKey("process_versions.id"), nullable=False
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("integration_status", sa.String(32), nullable=False, server_default="unknown"),
        sa.Column(
            "integration_evidence_id", sa.Uuid(), sa.ForeignKey("evidences.id"), nullable=True
        ),
    )
    op.create_index("ix_systems_organization_id", "systems", ["organization_id"])
    op.create_index("ix_systems_process_version_id", "systems", ["process_version_id"])
    op.create_table(
        "process_steps",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column(
            "process_version_id", sa.Uuid(), sa.ForeignKey("process_versions.id"), nullable=False
        ),
        sa.Column("step_key", sa.String(16), nullable=False),
        sa.Column("sequence_no", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("actors.id"), nullable=True),
        sa.Column("system_id", sa.Uuid(), sa.ForeignKey("systems.id"), nullable=True),
        sa.Column("manual", sa.Boolean(), nullable=True),
        sa.Column("duration_minutes", sa.Float(), nullable=True),
        sa.Column(
            "data_json", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.UniqueConstraint("process_version_id", "step_key", name="uq_step_key_per_version"),
    )
    op.create_index("ix_process_steps_organization_id", "process_steps", ["organization_id"])
    op.create_index(
        "ix_process_steps_version", "process_steps", ["process_version_id", "sequence_no"]
    )


def downgrade():
    op.drop_table("process_steps")
    op.drop_table("systems")
    op.drop_table("evidences")
    op.drop_table("actors")
    op.drop_constraint("uq_analysis_idempotency", "analysis_runs", type_="unique")
    op.drop_table("analysis_runs")
