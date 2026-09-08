"""P2 actual benefit tracking."""

import sqlalchemy as sa
from alembic import op

revision = "0011_benefit_realization"
down_revision = "0010_scoring_configurations"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "benefit_realizations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("opportunity_id", sa.Uuid(), sa.ForeignKey("opportunities.id"), nullable=False),
        sa.Column("period", sa.String(7), nullable=False),
        sa.Column("hours_saved", sa.Float()),
        sa.Column("monetary_benefit", sa.Float()),
        sa.Column("notes", sa.Text()),
        sa.Column("recorded_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("opportunity_id", "period", name="uq_benefit_realization_period"),
    )
    op.create_index(
        "ix_benefit_realizations_organization_id", "benefit_realizations", ["organization_id"]
    )


def downgrade():
    op.drop_table("benefit_realizations")
