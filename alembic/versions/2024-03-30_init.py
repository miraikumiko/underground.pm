"""init

Revision ID: ff4eb92d9c82
Revises: 
Create Date: 2024-03-30 17:32:12.326374

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff4eb92d9c82'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('ipv4',
    sa.Column('ip', sa.String(), nullable=False),
    sa.Column('available', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('ip')
    )
    op.create_index(op.f('ix_ipv4_ip'), 'ipv4', ['ip'], unique=True)
    op.create_table('ipv6',
    sa.Column('ip', sa.String(), nullable=False),
    sa.Column('available', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('ip')
    )
    op.create_index(op.f('ix_ipv6_ip'), 'ipv6', ['ip'], unique=True)
    op.create_table('server_ip',
    sa.Column('ip', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('ip')
    )
    op.create_index(op.f('ix_server_ip_ip'), 'server_ip', ['ip'], unique=True)
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(), nullable=False),
    sa.Column('email', sa.String(), nullable=True),
    sa.Column('hashed_password', sa.String(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('is_superuser', sa.Boolean(), nullable=False),
    sa.Column('is_verified', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=False)
    op.create_index(op.f('ix_user_id'), 'user', ['id'], unique=False)
    op.create_index(op.f('ix_user_is_active'), 'user', ['is_active'], unique=False)
    op.create_index(op.f('ix_user_is_superuser'), 'user', ['is_superuser'], unique=False)
    op.create_index(op.f('ix_user_is_verified'), 'user', ['is_verified'], unique=False)
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=True)
    op.create_table('discount',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('discount', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_discount_id'), 'discount', ['id'], unique=False)
    op.create_index(op.f('ix_discount_user_id'), 'discount', ['user_id'], unique=False)
    op.create_table('server',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('cores', sa.Integer(), nullable=False),
    sa.Column('ram', sa.Integer(), nullable=False),
    sa.Column('disk_type', sa.String(), nullable=False),
    sa.Column('disk_size', sa.Integer(), nullable=False),
    sa.Column('traffic', sa.Integer(), nullable=False),
    sa.Column('location', sa.String(), nullable=False),
    sa.Column('ipv4', sa.String(), nullable=True),
    sa.Column('ipv6', sa.String(), nullable=True),
    sa.Column('start_at', sa.TIMESTAMP(), nullable=False),
    sa.Column('end_at', sa.TIMESTAMP(), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_server_active'), 'server', ['active'], unique=False)
    op.create_index(op.f('ix_server_id'), 'server', ['id'], unique=False)
    op.create_index(op.f('ix_server_ipv4'), 'server', ['ipv4'], unique=True)
    op.create_index(op.f('ix_server_ipv6'), 'server', ['ipv6'], unique=True)
    op.create_table('user_settings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('notifications', sa.Boolean(), nullable=False),
    sa.Column('reset_password', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_settings_id'), 'user_settings', ['id'], unique=False)
    op.create_index(op.f('ix_user_settings_notifications'), 'user_settings', ['notifications'], unique=False)
    op.create_index(op.f('ix_user_settings_reset_password'), 'user_settings', ['reset_password'], unique=False)
    op.create_table('payment',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('server_id', sa.Integer(), nullable=True),
    sa.Column('amount', sa.BigInteger(), nullable=False),
    sa.Column('month', sa.Integer(), nullable=False),
    sa.Column('payment_uri', sa.String(), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['server_id'], ['server.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payment_active'), 'payment', ['active'], unique=False)
    op.create_index(op.f('ix_payment_id'), 'payment', ['id'], unique=False)
    op.create_index(op.f('ix_payment_payment_uri'), 'payment', ['payment_uri'], unique=False)
    op.create_index(op.f('ix_payment_server_id'), 'payment', ['server_id'], unique=False)
    op.create_index(op.f('ix_payment_user_id'), 'payment', ['user_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_payment_user_id'), table_name='payment')
    op.drop_index(op.f('ix_payment_server_id'), table_name='payment')
    op.drop_index(op.f('ix_payment_payment_uri'), table_name='payment')
    op.drop_index(op.f('ix_payment_id'), table_name='payment')
    op.drop_index(op.f('ix_payment_active'), table_name='payment')
    op.drop_table('payment')
    op.drop_index(op.f('ix_user_settings_reset_password'), table_name='user_settings')
    op.drop_index(op.f('ix_user_settings_notifications'), table_name='user_settings')
    op.drop_index(op.f('ix_user_settings_id'), table_name='user_settings')
    op.drop_table('user_settings')
    op.drop_index(op.f('ix_server_ipv6'), table_name='server')
    op.drop_index(op.f('ix_server_ipv4'), table_name='server')
    op.drop_index(op.f('ix_server_id'), table_name='server')
    op.drop_index(op.f('ix_server_active'), table_name='server')
    op.drop_table('server')
    op.drop_index(op.f('ix_discount_user_id'), table_name='discount')
    op.drop_index(op.f('ix_discount_id'), table_name='discount')
    op.drop_table('discount')
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_index(op.f('ix_user_is_verified'), table_name='user')
    op.drop_index(op.f('ix_user_is_superuser'), table_name='user')
    op.drop_index(op.f('ix_user_is_active'), table_name='user')
    op.drop_index(op.f('ix_user_id'), table_name='user')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')
    op.drop_index(op.f('ix_server_ip_ip'), table_name='server_ip')
    op.drop_table('server_ip')
    op.drop_index(op.f('ix_ipv6_ip'), table_name='ipv6')
    op.drop_table('ipv6')
    op.drop_index(op.f('ix_ipv4_ip'), table_name='ipv4')
    op.drop_table('ipv4')
    # ### end Alembic commands ###