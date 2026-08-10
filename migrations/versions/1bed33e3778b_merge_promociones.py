"""merge promociones

Revision ID: 1bed33e3778b
Revises: 6f95190c7070, a703da909e7e
Create Date: 2026-07-30 00:26:18.891506

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1bed33e3778b'
down_revision: Union[str, None] = ('6f95190c7070', 'a703da909e7e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
