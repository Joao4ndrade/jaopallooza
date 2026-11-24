"""foto de perfil

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-24 23:32:35.435835
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0004'
down_revision: str | None = '0003'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('user_photos',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('data', sa.LargeBinary(), nullable=False),
    sa.Column('content_type', sa.String(length=40), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_photos_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', name=op.f('pk_user_photos'))
    )
    op.add_column('users', sa.Column('photo_key', sa.String(length=32), nullable=True))
    op.create_unique_constraint(op.f('uq_users_photo_key'), 'users', ['photo_key'])


def downgrade() -> None:
    op.drop_constraint(op.f('uq_users_photo_key'), 'users', type_='unique')
    op.drop_column('users', 'photo_key')
    op.drop_table('user_photos')
