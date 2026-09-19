"""Add performance indexes

Revision ID: c5ce8c99c5ae
Revises: 001
Create Date: 2026-09-19 00:29:16.935441

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c5ce8c99c5ae'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Les index simples sont déjà définis dans les modèles
    # Cette migration est vide car les index sont gérés par SQLAlchemy
    pass


def downgrade():
    pass
