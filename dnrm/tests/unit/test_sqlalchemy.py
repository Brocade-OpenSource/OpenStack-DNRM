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
import sqlalchemy

from dnrm.db import sqlalchemy as db
from dnrm.db.sqlalchemy import models
from dnrm import exceptions
from dnrm.tests import base


class FakeModel(models.BASE):
    __tablename__ = 'fake'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String(255))
    group = sqlalchemy.Column(sqlalchemy.Integer)
    enabled = sqlalchemy.Column(sqlalchemy.Boolean)
    pool = sqlalchemy.Column(sqlalchemy.String(255))


class FiltersTestCase(base.BaseTestCase):
    def test_fields(self):
        cond = db.filters_to_condition(FakeModel, ['name'], {'name': 'abc',
                                                             'group': 1})
        self.assertEqual('fake.name = :name_1', str(cond))

    def test_fake_fields(self):
        self.assertRaises(AttributeError, db.filters_to_condition, FakeModel,
                          ['fake'], {})

    def test_in(self):
        cond = db.filters_to_condition(FakeModel, ['group'], {'group': (1, 2)})
        self.assertEqual('fake."group" IN (:group_1, :group_2)', str(cond))

    def test_equal(self):
        cond = db.filters_to_condition(FakeModel, ['name'], {'name': 'abc'})
        self.assertEqual('fake.name = :name_1', str(cond))

    def test_bool(self):
        cond = db.filters_to_condition(FakeModel, ['enabled'],
                                       {'enabled': True})
        self.assertEqual('fake.enabled = :enabled_1', str(cond))

    def test_none(self):
        cond = db.filters_to_condition(FakeModel, ['name'], {})
        self.assertIsNone(cond)

    def test_unused(self):
        cond = db.filters_to_condition(FakeModel, [], {'unused': True})
        self.assertEqual('fake.pool IS NULL', str(cond))

        cond = db.filters_to_condition(FakeModel, [], {'unused': 'True'})
        self.assertEqual('fake.pool IS NULL', str(cond))

        cond = db.filters_to_condition(FakeModel, [], {'unused': False})
        self.assertEqual('fake.pool IS NOT NULL', str(cond))

        cond = db.filters_to_condition(FakeModel, [], {'unused': 'False'})
        self.assertEqual('fake.pool IS NOT NULL', str(cond))


class ResourceTestCase(base.DBBaseTestCase):
    @staticmethod
    def _create(resource_type='fake-resource-type'):
        res = db.resource_create(resource_type, {'type': 'fake-driver',
                                                 'class': 'L3'})
        return res

    def test_create(self):
        res = self._create()
        self.assertEqual('fake-resource-type', res['type'])

    def test_delete(self):
        res = self._create()
        db.resource_delete(res['id'])
        self.assertRaises(exceptions.ResourceNotFound, db.resource_delete,
                          res['id'])

    def test_update(self):
        res = self._create()
        res = db.resource_update(res['id'], {'processing': True})
        self.assertTrue(res['processing'])

    def test_get_by_id(self):
        res = self._create()
        res2 = db.resource_get_by_id(res['id'])
        self.assertDictEqual(res, res2)

    def test_count(self):
        self._create()
        self._create()
        self._create('fake-resource-type-2')
        count = db.resource_count(
            {'filters': {'type': 'fake-resource-type'}}
        )
        self.assertEqual(2, count)

    def test_find(self):
        resources = [self._create() for _i in range(2)]
        self._create('fake-resource-type-2')
        resources2 = db.resource_find(
            {'filters': {'type': 'fake-resource-type'}}
        )
        self.assertEqual(2, len(resources2))
        for i, r in enumerate(resources):
            self.assertDictEqual(r, dict(resources2[i]))

    def test_compare_update(self):
        resource1 = self._create()
        values = {'processing': not resource1['processing']}
        resource2 = db.resource_compare_update(resource1['id'], {}, values)
        resource1.update(values)
        self.assertDictEqual(resource1, resource2)

    def test_compare_not_update(self):
        resource1 = self._create()
        values = {'processing': not resource1['processing']}
        filters = {'allocated': not resource1['allocated']}
        resource2 = db.resource_compare_update(resource1['id'], filters,
                                               values)
        self.assertIsNone(resource2)

    def test_compare_update_updates_right_resource(self):
        self._create()
        resource2 = self._create()
        self._create()
        values = {'status': 'ERROR'}
        filters = {'allocated': resource2['allocated']}
        retval = db.resource_compare_update(resource2['id'], filters, values)
        self.assertIsNotNone(retval)
        resource2 = db.resource_get_by_id(resource2['id'])
        self.assertEqual('ERROR', resource2['status'])
