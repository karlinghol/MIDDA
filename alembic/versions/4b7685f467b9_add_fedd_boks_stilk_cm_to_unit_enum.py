"""add fedd boks stilk cm to unit enum

Revision ID: 4b7685f467b9
Revises: 14a76c5f9811
Create Date: 2026-09-08 20:23:16.953365

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b7685f467b9'
down_revision: Union[str, Sequence[str], None] = '14a76c5f9811'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


old_values = ("G", "KG", "ML", "DL", "L", "TS", "SS", "STK", "KLYPE")
new_values = old_values + ("FEDD", "BOKS", "STILK", "CM")

old_enum = sa.Enum(*old_values, name="unit")
new_enum = sa.Enum(*new_values, name="unit")


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("dish_ingredients") as batch_op:
        batch_op.alter_column(
            "unit",
            existing_type=old_enum,
            type_=new_enum,
            existing_nullable=False,
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("dish_ingredients") as batch_op:
        batch_op.alter_column(
            "unit",
            existing_type=new_enum,
            type_=old_enum,
            existing_nullable=False,
        )
