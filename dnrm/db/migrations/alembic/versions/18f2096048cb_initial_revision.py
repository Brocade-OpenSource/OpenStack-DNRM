"""initial revision

Revision ID: 18f2096048cb
Revises: None
Create Date: 2013-09-16 14:38:57.905416

"""

# revision identifiers, used by Alembic.
revision = '18f2096048cb'
down_revision = None

from alembic import op
import sqlalchemy as sa


STATES = ('stopped',
          'started',
          'error')


def upgrade():
    op.create_table(
        'resources',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('resource_type', sa.String(length=250), nullable=False),
        sa.Column('state', sa.Enum(*STATES), default='stopped'),
        sa.Column('pool', sa.String(length=250), nullable=True),
        sa.Column('processing', sa.Boolean(), nullable=False, default=False),
        sa.Column('data', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'))


def downgrade():
    op.drop_table('resources')

