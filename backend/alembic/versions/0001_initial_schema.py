"""initial schema

Revision ID: 0001
Revises: 
Create Date: 2026-11-22 23:49:31.001374
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0001'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('award_categories',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=60), nullable=False),
    sa.Column('title', sa.String(length=80), nullable=False),
    sa.Column('description', sa.String(length=240), nullable=True),
    sa.Column('emoji', sa.String(length=16), server_default='🏆', nullable=False),
    sa.Column('kind', sa.String(length=20), server_default='individual', nullable=False),
    sa.Column('position', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.CheckConstraint("kind IN ('individual', 'couple')", name=op.f('ck_award_categories_kind')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_award_categories')),
    sa.UniqueConstraint('slug', name=op.f('uq_award_categories_slug'))
    )
    op.create_table('event_info',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=80), nullable=False),
    sa.Column('tagline', sa.String(length=160), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('starts_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('ends_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('venue_name', sa.String(length=120), nullable=True),
    sa.Column('venue_address', sa.String(length=200), nullable=True),
    sa.Column('city', sa.String(length=80), nullable=True),
    sa.Column('maps_url', sa.String(length=500), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('id = 1', name=op.f('ck_event_info_single_row')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_event_info'))
    )
    op.create_table('users',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('name', sa.String(length=30), nullable=False),
    sa.Column('name_key', sa.String(length=30), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('awards_opt_in', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('partner_id', sa.Uuid(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['partner_id'], ['users.id'], name=op.f('fk_users_partner_id_users'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
    sa.UniqueConstraint('name_key', name=op.f('uq_users_name_key'))
    )
    op.create_table('couples',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_a_id', sa.Uuid(), nullable=False),
    sa.Column('user_b_id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('user_a_id < user_b_id', name=op.f('ck_couples_ordered_pair')),
    sa.ForeignKeyConstraint(['user_a_id'], ['users.id'], name=op.f('fk_couples_user_a_id_users'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_b_id'], ['users.id'], name=op.f('fk_couples_user_b_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_couples')),
    sa.UniqueConstraint('user_a_id', 'user_b_id', name='uq_couples_pair')
    )
    op.create_table('tickets',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('code', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('checked_in_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_tickets_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_tickets')),
    sa.UniqueConstraint('code', name=op.f('uq_tickets_code')),
    sa.UniqueConstraint('user_id', name=op.f('uq_tickets_user_id'))
    )
    op.create_table('votes',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('voter_id', sa.Uuid(), nullable=False),
    sa.Column('category_id', sa.Integer(), nullable=False),
    sa.Column('nominee_user_id', sa.Uuid(), nullable=True),
    sa.Column('nominee_couple_id', sa.Uuid(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('(nominee_user_id IS NULL) <> (nominee_couple_id IS NULL)', name=op.f('ck_votes_one_nominee')),
    sa.ForeignKeyConstraint(['category_id'], ['award_categories.id'], name=op.f('fk_votes_category_id_award_categories'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['nominee_couple_id'], ['couples.id'], name=op.f('fk_votes_nominee_couple_id_couples'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['nominee_user_id'], ['users.id'], name=op.f('fk_votes_nominee_user_id_users'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['voter_id'], ['users.id'], name=op.f('fk_votes_voter_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_votes')),
    sa.UniqueConstraint('voter_id', 'category_id', name='uq_votes_one_per_category')
    )


def downgrade() -> None:
    op.drop_table('votes')
    op.drop_table('tickets')
    op.drop_table('couples')
    op.drop_table('users')
    op.drop_table('event_info')
    op.drop_table('award_categories')
