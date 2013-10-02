# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 OpenStack Foundation.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
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


STATES = ('STOPPED', 'STARTED', 'ERROR', 'DELETED', 'STARTING', 'STOPPING',
          'DELETING', 'WIPING')


def upgrade():
    op.create_table(
        'resources',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('type', sa.String(length=250), nullable=False),
        sa.Column('klass', sa.String(length=250), nullable=False),
        sa.Column('status', sa.Enum(*STATES), default='STOPPED'),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('data', sa.Text(), nullable=True),
        sa.Column('pool', sa.String(length=250), nullable=True),
        sa.Column('processing', sa.Boolean(), nullable=False, default=False),
        sa.Column('allocated', sa.Boolean(), nullable=False, default=False),
        sa.Column('deleted', sa.Boolean(), nullable=False, default=False),
        sa.PrimaryKeyConstraint('id'))


def downgrade():
    op.drop_table('resources')

