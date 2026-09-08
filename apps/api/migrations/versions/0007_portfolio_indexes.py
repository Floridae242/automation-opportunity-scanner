"""Add organization-scoped indexes used by portfolio ranking queries."""

from alembic import op

revision = "0007_portfolio_indexes"
down_revision = "0006_advice"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_projects_organization_department", "projects", ["organization_id", "department"]
    )
    op.create_index(
        "ix_opportunities_organization_analysis",
        "opportunities",
        ["organization_id", "analysis_run_id"],
    )
    op.create_index(
        "ix_opportunity_scores_organization_opportunity_created",
        "opportunity_scores",
        ["organization_id", "opportunity_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_opportunity_scores_organization_opportunity_created")
    op.drop_index("ix_opportunities_organization_analysis")
    op.drop_index("ix_projects_organization_department")
