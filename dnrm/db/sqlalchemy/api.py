# vim: tabstop=4 shiftwidth=4 softtabstop=4
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


def model_query(model, session=None, **kwargs):
    session = session or db_session.get_session()
    query = session.query(model)
    return query


def resource_create(resource_type, resource_data):
    resource = models.Resource(type=resource_type,
                               data=resource_data)
    resource.save()
    return resource


def _resource_get_by_id(id, session=None):
    task = (model_query(models.Resource, session=session)
            .filter_by(id=id)
            .first())
    if not task:
        raise exceptions.ResourceNotFound(id=id)
    return task


def resource_get_by_id(id):
    return _resource_get_by_id(id)


def resource_update(id, values):
    values = values.copy()
    validated_values = {}
    for key in (models.Resource.FILTER_FIELDS):
        try:
            validated_values[key] = values.pop(key)
        except KeyError:
            pass

    session = db_session.get_session()
    with session.begin():
        resource = _resource_get_by_id(id, session=session)
        if values:
            data = resource['data']
            data.update(values)
            validated_values['data'] = data
        resource.update(validated_values)

    return resource


def resource_delete(id):
    count = (model_query(models.Resource)
             .filter_by(id=id)
             .delete())
    if not count:
        raise exceptions.ResourceNotFound(id=id)


def filters_to_sa_condition(model, filter_fields, filter_values):
    columns = model
    filter_values = filter_values.copy()
    and_list = []
    for key in filter_fields:
        try:
            column = getattr(columns, key)
            value = filter_values.pop(key, None)
            if value is None:
                continue
            if type(value) == list:
                expr = column.in_(tuple(value))
            else:
                expr = (column == value)
            and_list.append(expr)
        except KeyError:
            pass
    if and_list:
        return sa.and_(*and_list)
    else:
        return None


def make_query(model, kwargs):
    kwargs = kwargs.copy()

    filters = kwargs.pop('filters', {})
    limit = kwargs.pop('limit', None)
    offset = kwargs.pop('offset', None)

    if kwargs:
        raise ValueError(_('Unexpected kwargs: %s') % ', '.join(kwargs.keys()))

    query = model_query(models.Resource)

    condition = filters_to_sa_condition(
        model,
        model.FILTER_FIELDS,
        filters)

    if condition is not None:
        query = query.filter(condition)

    if offset is not None:
        query = query.offset(limit)

    if limit is not None:
        query = query.limit(limit)

    return query


def resource_find(kwargs):
    query = make_query(
        models.Resource,
        kwargs)
    return query.all()


def resource_count(kwargs):
    query = make_query(
        models.Resource,
        kwargs)
    return query.count()
