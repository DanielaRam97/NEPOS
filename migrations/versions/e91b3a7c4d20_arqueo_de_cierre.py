"""Agrega arqueo y diferencia al cierre de turno.

Revision ID: e91b3a7c4d20
Revises: c8a4d1f0e2b3
"""

from alembic import op
import sqlalchemy as sa


revision = "e91b3a7c4d20"
down_revision = "c8a4d1f0e2b3"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "turnos",
        sa.Column("efectivo_declarado", sa.Numeric(12, 2), nullable=True),
    )
    op.add_column(
        "turnos",
        sa.Column("diferencia_caja", sa.Numeric(12, 2), nullable=True),
    )
    op.add_column(
        "turnos",
        sa.Column("observacion_cierre", sa.String(250), nullable=True),
    )
    op.add_column(
        "turnos",
        sa.Column("cerrado_por_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_turnos_cerrado_por_id_usuarios",
        "turnos",
        "usuarios",
        ["cerrado_por_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint(
        "fk_turnos_cerrado_por_id_usuarios",
        "turnos",
        type_="foreignkey",
    )
    op.drop_column("turnos", "cerrado_por_id")
    op.drop_column("turnos", "observacion_cierre")
    op.drop_column("turnos", "diferencia_caja")
    op.drop_column("turnos", "efectivo_declarado")
