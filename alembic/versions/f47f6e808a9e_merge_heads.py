"""merge heads

Revision ID: f47f6e808a9e
Revises: 002_add_personalized_learning_tables, c5ef93741107
Create Date: 2025-07-14 01:11:32.951395

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f47f6e808a9e'
down_revision: Union[str, Sequence[str], None] = ('002', 'c5ef93741107')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
