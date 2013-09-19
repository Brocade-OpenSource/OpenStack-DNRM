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
from dnrm.db import sqlalchemy as db
from dnrm import exceptions
from dnrm.tests import base


class ResourceTestCase(base.DBBaseTestCase):
    def setUp(self):
        super(ResourceTestCase, self).setUp()

    def test_create(self):
        res = db.resource_create('fake-resource-type', {})
        self.assertEqual('fake-resource-type', res['type'])

    def test_delete(self):
        res = db.resource_create('fake-resource-type', {})
        db.resource_delete(res['id'])
        self.assertRaises(exceptions.ResourceNotFound, db.resource_delete,
                          res['id'])

    def test_update(self):
        res = db.resource_create('fake-resource-type', {})
        res = db.resource_update(res['id'], {'processing': True})
        self.assertTrue(res['processing'])

    def test_get_by_id(self):
        res = dict(db.resource_create('fake-resource-type', {}))
        res2 = dict(db.resource_get_by_id(res['id']))
        self.assertDictEqual(res, res2)

    def test_count(self):
        db.resource_create('fake-resource-type', {})
        db.resource_create('fake-resource-type', {})
        db.resource_create('fake-resource-type-2', {})
        count = db.resource_count(
            {'filters': {'type': 'fake-resource-type'}}
        )
        self.assertEqual(2, count)

    def test_find(self):
        resources = [dict(db.resource_create('fake-resource-type', {}))
                     for _i in range(2)]
        db.resource_create('fake-resource-type-2', {})
        resources2 = db.resource_find(
            {'filters': {'type': 'fake-resource-type'}}
        )
        self.assertEqual(2, len(resources2))
        for i, r in enumerate(resources):
            self.assertDictEqual(r, dict(resources2[i]))
