"""P1 immutable organization scoring configurations."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0010_scoring_configurations"
down_revision = "0009_comments"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "scoring_configurations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("weights_json", postgresql.JSONB(), nullable=False),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint(
            "organization_id", "version_no", name="uq_scoring_configuration_version"
        ),
    )
    op.create_index(
        "ix_scoring_configurations_organization_id", "scoring_configurations", ["organization_id"]
    )
    op.execute(
        """
        CREATE FUNCTION prevent_scoring_configuration_mutation()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'scoring configurations are append-only';
        END;
        $$ LANGUAGE plpgsql;
        CREATE TRIGGER scoring_configurations_append_only
        BEFORE UPDATE OR DELETE ON scoring_configurations
        FOR EACH ROW EXECUTE FUNCTION prevent_scoring_configuration_mutation();
        """
    )
    op.add_column(
        "analysis_runs",
        sa.Column(
            "scoring_configuration_id", sa.Uuid(), sa.ForeignKey("scoring_configurations.id")
        ),
    )
    op.create_index(
        "ix_analysis_runs_scoring_configuration_id", "analysis_runs", ["scoring_configuration_id"]
    )
    op.add_column(
        "opportunity_scores",
        sa.Column(
            "scoring_configuration_id", sa.Uuid(), sa.ForeignKey("scoring_configurations.id")
        ),
    )
    op.create_index(
        "ix_opportunity_scores_scoring_configuration_id",
        "opportunity_scores",
        ["scoring_configuration_id"],
    )


def downgrade():
    op.execute("DROP TRIGGER scoring_configurations_append_only ON scoring_configurations")
    op.execute("DROP FUNCTION prevent_scoring_configuration_mutation()")
    op.drop_index("ix_opportunity_scores_scoring_configuration_id", table_name="opportunity_scores")
    op.drop_column("opportunity_scores", "scoring_configuration_id")
    op.drop_index("ix_analysis_runs_scoring_configuration_id", table_name="analysis_runs")
    op.drop_column("analysis_runs", "scoring_configuration_id")
    op.drop_table("scoring_configurations")
