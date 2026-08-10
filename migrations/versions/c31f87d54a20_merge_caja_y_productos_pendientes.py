"""une las ramas de caja y productos pendientes

Revision ID: c31f87d54a20
Revises: a71c9e4f2031, b84d91a06f72
"""
from typing import Sequence, Union


revision: str = "c31f87d54a20"
down_revision: Union[str, Sequence[str], None] = (
    "a71c9e4f2031",
    "b84d91a06f72",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Esta migración solo une las dos ramas. No modifica tablas.
    pass


def downgrade() -> None:
    # Al bajar, Alembic vuelve a considerar ambas revisiones como heads.
    pass
