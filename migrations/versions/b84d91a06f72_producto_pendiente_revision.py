"""producto pendiente de revision

Revision ID: b84d91a06f72
Revises: 642691d130ad
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b84d91a06f72"
down_revision: Union[str, None] = "642691d130ad"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "productos",
        sa.Column(
            "pendiente_revision",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "productos",
        sa.Column("solicitado_por_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "productos",
        sa.Column("fecha_solicitud", sa.DateTime(), nullable=True),
    )
    op.create_foreign_key(
        "fk_productos_solicitado_por",
        "productos",
        "usuarios",
        ["solicitado_por_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_productos_solicitado_por",
        "productos",
        type_="foreignkey",
    )
    op.drop_column("productos", "fecha_solicitud")
    op.drop_column("productos", "solicitado_por_id")
    op.drop_column("productos", "pendiente_revision")
