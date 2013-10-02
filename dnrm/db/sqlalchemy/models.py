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

"""
SQLAlchemy models for DNRM data.
"""

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

from dnrm.db.sqlalchemy import types
from dnrm.openstack.common.db.sqlalchemy import models
from dnrm.openstack.common.db.sqlalchemy import session as db_session
from dnrm.openstack.common import uuidutils
from dnrm.resources import base


BASE = declarative_base()


UUID_LENGTH = 36


def create_db():
    BASE.metadata.create_all(db_session.get_engine())


def drop_db():
    engine = db_session.get_engine()
    OLD_BASE = declarative_base()
    OLD_BASE.metadata.reflect(bind=engine)
    OLD_BASE.metadata.drop_all(engine, checkfirst=True)


class DNRMBase(models.ModelBase):
    __table_args__ = {'mysql_engine': 'InnoDB'}


class HasId(object):
    """id mixin, add to subclasses that have an id."""

    id = sa.Column(sa.String(UUID_LENGTH),
                   primary_key=True,
                   default=uuidutils.generate_uuid)


class Resource(BASE, DNRMBase, HasId):
    __tablename__ = 'resources'

    STATES = (base.STATE_STARTED, base.STATE_STOPPED, base.STATE_ERROR,
              base.STATE_DELETED, base.STATE_STARTING, base.STATE_STOPPING,
              base.STATE_DELETING, base.STATE_WIPING)

    MAX_RESOURCE_TYPE_LENGTH = 250

    FILTER_FIELDS = ['type', 'status', 'pool', 'processing', 'allocated',
                     'deleted', 'description', 'klass']

    type = sa.Column(sa.String(MAX_RESOURCE_TYPE_LENGTH), nullable=False)
    klass = sa.Column(sa.String(MAX_RESOURCE_TYPE_LENGTH), nullable=False)
    status = sa.Column(sa.Enum(*STATES), nullable=False,
                       default=base.STATE_STOPPED)
    description = sa.Column(sa.Text)
    data = sa.Column(types.JSON(), default={})

    pool = sa.Column(sa.String(MAX_RESOURCE_TYPE_LENGTH), nullable=True)
    processing = sa.Column(sa.Boolean, nullable=False, default=False)
    allocated = sa.Column(sa.Boolean, nullable=False, default=False)
    deleted = sa.Column(sa.Boolean, nullable=False, default=False)
