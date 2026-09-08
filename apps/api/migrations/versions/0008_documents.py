"""M6: untrusted process-document metadata and bounded extracted text."""

import sqlalchemy as sa
from alembic import op

revision = "0008_documents"
down_revision = "0007_portfolio_indexes"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "process_documents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("process_id", sa.Uuid(), sa.ForeignKey("processes.id"), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("media_type", sa.String(64), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=False),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_process_documents_organization_id", "process_documents", ["organization_id"]
    )
    op.create_index("ix_process_documents_process_id", "process_documents", ["process_id"])
    op.create_index(
        "ix_process_documents_organization_process_created",
        "process_documents",
        ["organization_id", "process_id", "created_at"],
    )


def downgrade():
    op.drop_table("process_documents")
