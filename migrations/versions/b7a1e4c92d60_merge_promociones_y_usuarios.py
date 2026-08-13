"""Une las ramas de promociones y auditoria de usuarios.

Revision ID: b7a1e4c92d60
Revises: 9afc6e40c5aa, 5c9e21d73a40
"""

from typing import Sequence, Union


revision: str = "b7a1e4c92d60"
down_revision: Union[str, Sequence[str], None] = (
    "9afc6e40c5aa",
    "5c9e21d73a40",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass