"""Make nullable project_id and task_id in ai-review

Revision ID: 6bbcc62f85e6
Revises: 34d42460359f
Create Date: 2026-03-08 20:08:40.276772

"""

from collections.abc import Sequence
from typing import Union

# revision identifiers, used by Alembic.
revision: str = "6bbcc62f85e6"
down_revision: Union[str, None] = "34d42460359f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
