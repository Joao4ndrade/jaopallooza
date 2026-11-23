"""email e recuperacao de senha

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-23 00:32:01.051453
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0003'
down_revision: str | None = '0002'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('password_reset_tokens',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_password_reset_tokens_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_password_reset_tokens')),
    sa.UniqueConstraint('token_hash', name=op.f('uq_password_reset_tokens_token_hash'))
    )
    op.create_index(op.f('ix_password_reset_tokens_user_id'), 'password_reset_tokens', ['user_id'], unique=False)
    op.add_column('users', sa.Column('email', sa.String(length=254), nullable=True))
    op.add_column('users', sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=True))
    op.create_unique_constraint(op.f('uq_users_email'), 'users', ['email'])


def downgrade() -> None:
    op.drop_constraint(op.f('uq_users_email'), 'users', type_='unique')
    op.drop_column('users', 'password_changed_at')
    op.drop_column('users', 'email')
    op.drop_index(op.f('ix_password_reset_tokens_user_id'), table_name='password_reset_tokens')
    op.drop_table('password_reset_tokens')
