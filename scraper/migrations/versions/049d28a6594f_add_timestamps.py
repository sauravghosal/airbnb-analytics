"""add timestamps

Revision ID: 049d28a6594f
Revises: 7e44ae985f8f
Create Date: 2022-04-06 13:27:25.537746

"""
from alembic import op
from sqlalchemy import TIMESTAMP, Column, text


# revision identifiers, used by Alembic.
revision = '049d28a6594f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('listing', Column('time_created', TIMESTAMP(timezone=True), nullable=False, server_default=text('CURRENT_TIMESTAMP')))
    op.add_column('listing', Column('time_updated', TIMESTAMP(timezone=True), nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')))
    op.add_column('location', Column('time_created', TIMESTAMP(timezone=True), nullable=False, server_default=text('CURRENT_TIMESTAMP')))


def downgrade():
    op.drop_column('listing', 'time_created')
    op.drop_column('listing', 'time_updated')
    op.drop_column('location', 'time_created')