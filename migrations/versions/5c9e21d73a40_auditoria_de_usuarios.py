"""Agrega trazabilidad y último acceso a usuarios.

Revision ID: 5c9e21d73a40
Revises: 0d74b0aa7ab5
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5c9e21d73a40"
down_revision: Union[str, None] = "0d74b0aa7ab5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "usuarios",
        sa.Column(
            "fecha_creacion",
            sa.DateTime(),
            nullable=True,
            server_default=sa.func.now(),
        ),
    )
    op.add_column(
        "usuarios",
        sa.Column("ultimo_acceso", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "usuarios",
        sa.Column("creado_por_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "usuarios",
        sa.Column("actualizado_por_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "usuarios",
        sa.Column(
            "fecha_actualizacion",
            sa.DateTime(),
            nullable=True,
            server_default=sa.func.now(),
        ),
    )
    op.create_foreign_key(
        "fk_usuarios_creado_por_id",
        "usuarios",
        "usuarios",
        ["creado_por_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_usuarios_actualizado_por_id",
        "usuarios",
        "usuarios",
        ["actualizado_por_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_usuarios_rol_activo",
        "usuarios",
        ["rol", "activo"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_usuarios_rol_activo", table_name="usuarios")
    op.drop_constraint(
        "fk_usuarios_actualizado_por_id",
        "usuarios",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_usuarios_creado_por_id",
        "usuarios",
        type_="foreignkey",
    )
    op.drop_column("usuarios", "fecha_actualizacion")
    op.drop_column("usuarios", "actualizado_por_id")
    op.drop_column("usuarios", "creado_por_id")
    op.drop_column("usuarios", "ultimo_acceso")
    op.drop_column("usuarios", "fecha_creacion")