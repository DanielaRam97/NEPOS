"""Mantiene la continuidad posterior a la migración de promociones.

La revisión 9f4c2b8a1d30 ya realizó los cambios de esquema necesarios.
Esta revisión queda vacía para evitar repetir la creación de tablas y columnas.

Revision ID: 9afc6e40c5aa
Revises: 9f4c2b8a1d30
Create Date: 2026-08-03 16:10:27.127438
"""

from typing import Sequence, Union


revision: str = "9afc6e40c5aa"
down_revision: Union[str, None] = "9f4c2b8a1d30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass