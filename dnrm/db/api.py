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

from dnrm.openstack.common.db import api as db_api
from dnrm.openstack.common import log as logging


_BACKEND_MAPPING = {'sqlalchemy': 'dnrm.db.sqlalchemy.api'}

IMPL = db_api.DBAPI(backend_mapping=_BACKEND_MAPPING)

LOG = logging.getLogger(__name__)


def db_create():
    """Initialize DB. This method will drop existing database."""
    IMPL.db_create()


def db_drop():
    """Drop DB. This method drop existing database."""
    IMPL.db_drop()


def db_cleanup():
    """Recreate engine."""
    IMPL.db_cleanup()


def resource_create(resource_type, resource_data):
    return IMPL.resource_create(resource_type, resource_data)


def resource_get_by_id(resource_id):
    return IMPL.resource_get_by_id(resource_id)


def resource_update(resource_id, resource_data):
    return IMPL.resource_update(resource_id, resource_data)


def resource_delete(resource_id):
    return IMPL.resource_delete(resource_id)


def resource_find(filter_opts={}):
    return IMPL.resource_find(filter_opts)


def resource_count(filter_opts={}):
    return IMPL.resource_count(filter_opts)
