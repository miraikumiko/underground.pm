"""update user settings

Revision ID: ebec8283ac3f
Revises: 2f61a0088572
Create Date: 2024-03-02 13:25:16.268020

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ebec8283ac3f'
down_revision: Union[str, None] = '2f61a0088572'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_user_settings_notifications', table_name='user_settings')
    op.create_index(op.f('ix_user_settings_notifications'), 'user_settings', ['notifications'], unique=False)
    op.drop_index('ix_user_settings_reset_password', table_name='user_settings')
    op.create_index(op.f('ix_user_settings_reset_password'), 'user_settings', ['reset_password'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_user_settings_reset_password'), table_name='user_settings')
    op.create_index('ix_user_settings_reset_password', 'user_settings', ['reset_password'], unique=True)
    op.drop_index(op.f('ix_user_settings_notifications'), table_name='user_settings')
    op.create_index('ix_user_settings_notifications', 'user_settings', ['notifications'], unique=True)
    # ### end Alembic commands ###
