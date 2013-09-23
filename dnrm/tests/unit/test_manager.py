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
from dnrm.resources import manager
from dnrm.tests import base


class ManagerTestCase(base.DBBaseTestCase):
    """ResourceFactory test case."""

    @classmethod
    def setUpClass(cls):
        super(ManagerTestCase, cls).setUpClass()
        cls.df = mock.Mock()
        cls.dv = mock.Mock()
        cls.df.get.return_value = cls.dv

    def setUp(self):
        super(ManagerTestCase, self).setUp()
        self.context = None
        self.useFixture(mockpatch.Patch('dnrm.drivers.factory.DriverFactory',
                                        return_value=self.df))

        self.db = self.useFixture(mockpatch.Patch('dnrm.resources.manager.'
                                                  'db')).mock

        self.tq = self.useFixture(mockpatch.Patch('dnrm.task_queue.'
                                                  'TaskQueue')).mock

        self.useFixture(mockpatch.Patch('dnrm.task_queue.QueuedTaskWorker'))

        self.bm = self.useFixture(mockpatch.Patch('dnrm.balancer.manager.'
                                                  'DNRMBalancersManager')).mock

        self.useFixture(mockpatch.Patch('dnrm.pools.pool.Pool'))
        self.useFixture(mockpatch.Patch('dnrm.pools.unused_set.UnusedSet'))

        self.useFixture(mockpatch.Patch('dnrm.resources.cleaner.Cleaner'))

        self.manager = manager.ResourceManager()

    def test_schema(self):
        self.dv.schema.return_value = 'fake-schema'
        schema = self.manager.schema(self.context, 'fake-driver')
        self.df.get.assert_called_once_with('fake-driver')
        self.assertEqual(1, self.df.get.call_count)
        self.assertEqual(1, self.dv.schema.call_count)
        self.assertEqual('fake-schema', schema)

    def test_get(self):
        self.db.resource_get_by_id.return_value = {'id': 'fake-resource-id'}
        resource = self.manager.get(self.context, 'fake-resource-id')
        self.db.resource_get_by_id.assert_called_once_with('fake-resource-id')
        self.assertEqual(1, self.db.resource_get_by_id.call_count)
        self.assertDictEqual({'id': 'fake-resource-id'}, resource)

    def test_get_list(self):
        self.db.resource_find.return_value = [{'id': 'fake-resource-id'}]
        resources = self.manager.list(self.context, {'id': 'fake-resource-id'})
        self.db.resource_find.assert_called_once_with(
            {'id': 'fake-resource-id'})
        self.assertEqual(1, self.db.resource_find.call_count)
        self.assertListEqual([{'id': 'fake-resource-id'}], resources)
