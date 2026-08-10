"""ingreso con costo, precio de venta y grupos

Revision ID: d42e81f73b06
Revises: c31f87d54a20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d42e81f73b06"
down_revision: Union[str, None] = "c31f87d54a20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "productos",
        sa.Column("grupo_precio", sa.String(100), nullable=True),
    )
    op.add_column(
        "ingresos",
        sa.Column(
            "precio_venta",
            sa.Numeric(12, 2, asdecimal=False),
            nullable=True,
        ),
    )
    op.add_column(
        "ingresos",
        sa.Column(
            "costo_anterior",
            sa.Numeric(12, 2, asdecimal=False),
            nullable=True,
        ),
    )
    op.add_column(
        "ingresos",
        sa.Column(
            "precio_anterior",
            sa.Numeric(12, 2, asdecimal=False),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("ingresos", "precio_anterior")
    op.drop_column("ingresos", "costo_anterior")
    op.drop_column("ingresos", "precio_venta")
    op.drop_column("productos", "grupo_precio")
