"""Add en_consultation field to Salle

Revision ID: 002
Revises: 001
Create Date: 2026-10-08

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('salle', sa.Column('en_consultation', sa.Boolean(), nullable=False, server_default='false'))


def downgrade():
    op.drop_column('salle', 'en_consultation')
