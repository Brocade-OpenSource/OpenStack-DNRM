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
import mock

from dnrm.openstack.common.fixture import mockpatch
from dnrm.pools import pool
from dnrm.pools import unused_set
from dnrm.tests import base


class PoolTestCase(base.BaseTestCase):
    def setUp(self):
        super(PoolTestCase, self).setUp()
        self.db = self.useFixture(mockpatch.Patch('dnrm.pools.pool.db')).mock
        self.pool_name = 'fake-pool'
        self.pool = pool.Pool(self.pool_name)

    def test_push(self):
        self.pool.push('fake-uuid')
        self.db.resource_update.assert_called_with('fake-uuid',
                                                   {'pool': self.pool_name,
                                                    'processing': False})

    def test_pop_one(self):
        resources = [{'id': 'fake-uuid', 'pool': self.pool_name}]
        self.db.resource_find.return_value = resources
        self.db.resource_update.return_value = {'pool': None,
                                                'processing': True}

        pop_resources = self.pool.pop()

        self.assertIsNone(pop_resources[0]['pool'])
        self.assertTrue(pop_resources[0]['processing'])

        self.db.resource_find.assert_called_with({
            'limit': 1,
            'filters': {'allocated': False, 'pool': self.pool_name}
        })
        self.db.resource_update.assert_called_with('fake-uuid',
                                                   {'pool': None,
                                                    'processing': True})

        self.assertEqual(1, self.db.resource_find.call_count)
        self.assertEqual(1, self.db.resource_update.call_count)

    def test_pop_two(self):
        resources = [{'id': 'fake-uuid-1', 'pool': self.pool_name},
                     {'id': 'fake-uuid-2', 'pool': self.pool_name}]
        self.db.resource_find.return_value = resources
        self.db.resource_update.return_value = {'pool': None,
                                                'processing': True}

        pop_resources = self.pool.pop(2)

        for resource in pop_resources:
            self.assertIsNone(resource['pool'])
            self.assertTrue(resource['processing'])

        self.db.resource_find.assert_called_with({
            'limit': 2,
            'filters': {'allocated': False, 'pool': self.pool_name}
        })

        self.assertEqual(1, self.db.resource_find.call_count)
        self.assertEqual(2, self.db.resource_update.call_count)

        calls = [mock.call('fake-uuid-1', {'pool': None, 'processing': True}),
                 mock.call('fake-uuid-2', {'pool': None, 'processing': True})]
        self.db.resource_update.assert_has_calls(calls)

    def test_list(self):
        resources = [{'id': 'fake-uuid-1', 'pool': self.pool_name},
                     {'id': 'fake-uuid-2', 'pool': self.pool_name}]
        self.db.resource_find.return_value = resources

        pop_resources = self.pool.list()

        self.assertListEqual(resources, pop_resources)
        self.db.resource_find.assert_called_with({'filters': {
            'pool': self.pool_name, 'allocated': False
        }})

        self.assertEqual(1, self.db.resource_find.call_count)

    def test_count(self):
        self.db.resource_count.return_value = 2

        count = self.pool.count()

        self.assertEqual(2, count)
        self.db.resource_count.assert_called_with({'filters': {
            'pool': self.pool_name, 'allocated': False
        }})


class UnusedSetTestCase(base.BaseTestCase):
    def setUp(self):
        super(UnusedSetTestCase, self).setUp()
        self.db = self.useFixture(
            mockpatch.Patch('dnrm.pools.unused_set.db')).mock
        self.dv = mock.Mock()
        self.dv.prepare_resource.return_value = {'id': 'id',
                                                 'status': 'STARTED'}
        df = mock.Mock()
        df.get.return_value = self.dv
        self.unused_set = unused_set.UnusedSet('fake-resource_type', df)

    def test_list_resources_exists(self):
        self.db.resource_find.return_value = [1, 2]
        self.unused_set.list('status', 2)
        filter_opts = {'filters': {'type': 'fake-resource_type',
                                   'pool': None,
                                   'allocated': False, 'processing': False,
                                   'deleted': False, 'status': 'status'},
                       'limit': 2}
        self.db.resource_find.assert_called_with(filter_opts)
        self.assertEqual(0, self.dv.prepare_resource.call_count)

    def test_list_resources_exists_with_none_count(self):
        self.db.resource_find.return_value = [1, 2]
        self.unused_set.list('status')
        filter_opts = {'filters': {'type': 'fake-resource_type',
                                   'pool': None,
                                   'allocated': False, 'processing': False,
                                   'deleted': False, 'status': 'status'}}
        self.db.resource_find.assert_called_with(filter_opts)
        self.assertEqual(0, self.dv.prepare_resource.call_count)

    def test_get_resources(self):
        self.db.resource_find.return_value = []
        self.db.resource_update.return_value = {'processing': True}
        self.unused_set.get('STARTED', 2)
        filter_opts = {'filters': {'type': 'fake-resource_type',
                                   'pool': None, 'allocated': False,
                                   'processing': False, 'deleted': False,
                                   'status': 'STARTED'},
                       'limit': 2}
        self.db.resource_find.assert_called_with(filter_opts)
        self.assertEqual(2, self.dv.prepare_resource.call_count)

    def test_count(self):
        self.db.resource_count.return_value = 10
        res = self.unused_set.count('status')
        self.db.resource_count.assert_called_with(
            {'filters': {'type': 'fake-resource_type', 'pool': None,
                         'allocated': False, 'status': 'status',
                         'processing': False, 'deleted': False}})
        self.assertEqual(1, self.db.resource_count.call_count)
        self.assertEqual(10, res)
