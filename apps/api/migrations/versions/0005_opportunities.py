"""M4 opportunity engine: pain points, opportunities, score snapshots."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0005_opportunities"
down_revision = "0004_extraction"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "pain_points",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("analysis_run_id", sa.Uuid(), sa.ForeignKey("analysis_runs.id"), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(8), nullable=False),
        sa.Column("confidence", sa.String(8), nullable=False),
        sa.Column(
            "evidence_json",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.create_index("ix_pain_points_organization_id", "pain_points", ["organization_id"])
    op.create_index("ix_pain_points_analysis_run_id", "pain_points", ["analysis_run_id"])
    op.create_table(
        "opportunities",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("analysis_run_id", sa.Uuid(), sa.ForeignKey("analysis_runs.id"), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column(
            "scope_json", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="candidate"),
        sa.Column(
            "result_state", sa.String(24), nullable=False, server_default="insufficient_evidence"
        ),
    )
    op.create_index("ix_opportunities_organization_id", "opportunities", ["organization_id"])
    op.create_index("ix_opportunities_analysis_run_id", "opportunities", ["analysis_run_id"])
    op.create_table(
        "opportunity_scores",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column(
            "opportunity_id",
            sa.Uuid(),
            sa.ForeignKey("opportunities.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("total_score", sa.Float(), nullable=True),
        sa.Column(
            "dimension_json",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("confidence_score", sa.Integer(), nullable=False),
        sa.Column("scoring_version", sa.String(64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_opportunity_scores_organization_id", "opportunity_scores", ["organization_id"]
    )


def downgrade():
    op.drop_table("opportunity_scores")
    op.drop_table("opportunities")
    op.drop_table("pain_points")
