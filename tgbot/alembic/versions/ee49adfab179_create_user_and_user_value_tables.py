"""create user and user_value tables

Revision ID: ee49adfab179
Revises: 
Create Date: 2024-08-12 12:45:09.943205

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = 'ee49adfab179'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Get the current bind engine
    bind = op.get_bind()
    # We use `Inspector.from_engine(bind.engine)` to get an Inspector from the Engine
    inspector = Inspector.from_engine(bind.engine)

    # Check if the 'users' table already exists before creating it
    if 'users' not in inspector.get_table_names():
        op.create_table(
            'users',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('tg_id', sa.BigInteger(), nullable=True)
        )

    # Check if the 'user_values' table already exists before creating it
    if 'user_values' not in inspector.get_table_names():
        op.create_table(
            'user_values',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('value', sa.String(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'])
        )


def downgrade() -> None:
    # Get the current bind engine
    bind = op.get_bind()
    # We use `Inspector.from_engine(bind.engine)` to get an Inspector from the Engine
    inspector = Inspector.from_engine(bind.engine)

    # Drop the 'user_values' table if it exists
    if 'user_values' in inspector.get_table_names():
        op.drop_table('user_values')

    # Drop the 'users' table if it exists
    if 'users' in inspector.get_table_names():
        op.drop_table('users')
