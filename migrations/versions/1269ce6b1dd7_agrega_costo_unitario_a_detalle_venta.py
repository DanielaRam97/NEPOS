"""agrega costo unitario a detalle venta

Revision ID: 1269ce6b1dd7
Revises: f2d6a8b13c40
Create Date: 2026-08-26 23:40:48.740239

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1269ce6b1dd7'
down_revision: Union[str, None] = 'f2d6a8b13c40'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "detalle_venta",
        sa.Column(
            "costo_unitario",
            sa.Numeric(12, 2, asdecimal=False),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("detalle_venta", "costo_unitario")