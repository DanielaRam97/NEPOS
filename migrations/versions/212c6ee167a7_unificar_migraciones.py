"""unificar migraciones

Revision ID: 212c6ee167a7
Revises: c23921f924bc, d42e81f73b06
Create Date: 2026-07-24 15:22:44.176510

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '212c6ee167a7'
down_revision: Union[str, None] = ('c23921f924bc', 'd42e81f73b06')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
