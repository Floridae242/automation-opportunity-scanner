"""P1 append-only discussion comments for process versions."""

import sqlalchemy as sa
from alembic import op

revision = "0009_comments"
down_revision = "0008_documents"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "process_version_comments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column(
            "process_version_id", sa.Uuid(), sa.ForeignKey("process_versions.id"), nullable=False
        ),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_process_version_comments_organization_id",
        "process_version_comments",
        ["organization_id"],
    )
    op.create_index(
        "ix_process_version_comments_process_version_id",
        "process_version_comments",
        ["process_version_id"],
    )
    op.create_index(
        "ix_process_version_comments_organization_version_created",
        "process_version_comments",
        ["organization_id", "process_version_id", "created_at"],
    )


def downgrade():
    op.drop_table("process_version_comments")
