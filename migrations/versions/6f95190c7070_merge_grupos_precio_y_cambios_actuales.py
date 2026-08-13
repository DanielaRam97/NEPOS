"""merge grupos precio y cambios actuales

Revision ID: 6f95190c7070
Revises: 212c6ee167a7, e53f91a84c27
Create Date: 2026-07-28 18:47:12.871331

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6f95190c7070'
down_revision: Union[str, None] = ('212c6ee167a7', 'e53f91a84c27')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
