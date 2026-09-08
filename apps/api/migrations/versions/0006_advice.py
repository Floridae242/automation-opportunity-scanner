"""M5: recommendations, ROI scenarios, executive report snapshots."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0006_advice"
down_revision = "0005_opportunities"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "recommendations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column(
            "opportunity_id",
            sa.Uuid(),
            sa.ForeignKey("opportunities.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "patterns_json",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column(
            "prerequisites_json",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "risks_json", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False
        ),
        sa.Column("human_control", sa.Text(), nullable=False),
        sa.Column(
            "rejected_alternatives_json",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("confidence", sa.String(8), nullable=False),
    )
    op.create_index("ix_recommendations_organization_id", "recommendations", ["organization_id"])
    op.create_table(
        "roi_scenarios",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column(
            "opportunity_id",
            sa.Uuid(),
            sa.ForeignKey("opportunities.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "input_json", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.Column(
            "output_json", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_roi_scenarios_organization_id", "roi_scenarios", ["organization_id"])
    op.create_table(
        "reports",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column(
            "analysis_run_id",
            sa.Uuid(),
            sa.ForeignKey("analysis_runs.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("status", sa.String(16), nullable=False, server_default="ready"),
        sa.Column(
            "snapshot_json",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("storage_key", sa.String(200), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_reports_organization_id", "reports", ["organization_id"])


def downgrade():
    op.drop_table("reports")
    op.drop_table("roi_scenarios")
    op.drop_table("recommendations")
