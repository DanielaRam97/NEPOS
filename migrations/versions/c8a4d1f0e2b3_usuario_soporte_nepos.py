"""Agrega identificación y protección a la cuenta técnica de NEPOS.

Revision ID: c8a4d1f0e2b3
Revises: b7a1e4c92d60
"""

from alembic import op
import sqlalchemy as sa


revision = "c8a4d1f0e2b3"
down_revision = "b7a1e4c92d60"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "usuarios",
        sa.Column(
            "es_soporte",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "usuarios",
        sa.Column(
            "protegido",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.create_index(
        "ix_usuarios_es_soporte",
        "usuarios",
        ["es_soporte"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_usuarios_es_soporte", table_name="usuarios")
    op.drop_column("usuarios", "protegido")
    op.drop_column("usuarios", "es_soporte")
