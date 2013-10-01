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
import copy
import sys

import sqlalchemy as sa

from dnrm.db.sqlalchemy import models
from dnrm.exceptions import db as exceptions
from dnrm.openstack.common.db.sqlalchemy import session as db_session


def get_backend():
    """The backend is this module itself."""
    return sys.modules[__name__]


def db_create():
    models.create_db()


def db_drop():
    models.drop_db()


def db_cleanup():
    db_session.cleanup()


def model_query(model, session=None):
    session = session or db_session.get_session()
    query = session.query(model)
    return query


def filters_to_condition(model, filter_fields, filter_values):
    filter_values = copy.deepcopy(filter_values)
    if 'class' in filter_values:
        filter_values['klass'] = filter_values.pop('class')
    and_list = []
    for key in filter_fields:
        column = getattr(model, key)
        if key not in filter_values:
            continue
        value = filter_values.pop(key)
        if (isinstance(value, bool) and
            not isinstance(column.property.columns[0].type, sa.Boolean)):
            expr = (column != None) if value else (column == None)
        elif isinstance(value, (list, tuple, set)):
            expr = column.in_(set(value))
        else:
            expr = (column == value)
        and_list.append(expr)
    if and_list:
        return sa.and_(*and_list)
    else:
        return None


###############################################################################
# Resources


def _resource_to_dict(resource):
    resource = dict(resource)
    resource['class'] = resource.pop('klass')
    data = resource.pop('data', {})
    resource.update(data)
    return resource


def _update_resource(resource, values):
    values = copy.deepcopy(values)
    if 'id' in values:
        del values['id']
    if 'class' in values:
        values['klass'] = values.pop('class')
    validated_values = {}
    for key in models.Resource.FILTER_FIELDS:
        try:
            validated_values[key] = values.pop(key)
        except KeyError:
            pass
    if values:
        data = copy.deepcopy(resource['data']) or {}
        data.update(values)
        validated_values['data'] = data
    resource.update(validated_values)


def resource_create(driver_name, values):
    resource = models.Resource()
    _update_resource(resource, values)
    resource['type'] = driver_name
    resource.save()
    return _resource_to_dict(resource)


def _resource_get_by_id(id, session=None):
    task = (model_query(models.Resource, session=session)
            .filter_by(id=id)
            .first())
    if not task:
        raise exceptions.ResourceNotFound(id=id)
    return task


def resource_get_by_id(id):
    return _resource_to_dict(_resource_get_by_id(id))


def resource_update(id, values):
    session = db_session.get_session()
    with session.begin():
        resource = _resource_get_by_id(id, session=session)
        _update_resource(resource, values)

    return _resource_to_dict(resource)


def resource_delete(id):
    count = (model_query(models.Resource)
             .filter_by(id=id)
             .delete())
    if not count:
        raise exceptions.ResourceNotFound(id=id)


def make_query(model, kwargs):
    kwargs = kwargs.copy()

    filters = kwargs.pop('filters', {})
    limit = kwargs.pop('limit', None)
    offset = kwargs.pop('offset', None)

    if kwargs:
        raise ValueError(_('Unexpected kwargs: %s') % ', '.join(kwargs.keys()))

    query = model_query(models.Resource)

    condition = filters_to_condition(model, model.FILTER_FIELDS, filters)

    if condition is not None:
        query = query.filter(condition)

    if offset is not None:
        query = query.offset(limit)

    if limit is not None:
        query = query.limit(limit)

    return query


def resource_find(kwargs):
    query = make_query(models.Resource, kwargs)
    return [_resource_to_dict(resource) for resource in query.all()]


def resource_count(kwargs):
    query = make_query(models.Resource, kwargs)
    return query.count()
