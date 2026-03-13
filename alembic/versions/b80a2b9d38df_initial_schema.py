"""initial schema

Revision ID: b80a2b9d38df
Revises:
Create Date: 2026-03-08 19:32:11.979780
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b80a2b9d38df'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('urls',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('short_code', sa.String(length=30), nullable=False),
    sa.Column('original_url', sa.Text(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('click_count', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_urls_short_code'), 'urls', ['short_code'], unique=True)

    op.create_table('click_events',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('url_id', sa.Integer(), nullable=False),
    sa.Column('clicked_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('user_agent', sa.Text(), nullable=True),
    sa.Column('browser', sa.String(length=100), nullable=True),
    sa.Column('os', sa.String(length=100), nullable=True),
    sa.Column('referrer', sa.Text(), nullable=True),
    sa.Column('country', sa.String(length=100), nullable=True),
    sa.ForeignKeyConstraint(['url_id'], ['urls.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_click_events_url_id'), 'click_events', ['url_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_click_events_url_id'), table_name='click_events')
    op.drop_table('click_events')
    op.drop_index(op.f('ix_urls_short_code'), table_name='urls')
    op.drop_table('urls')
