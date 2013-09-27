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
from oslo.config import cfg

from dnrm.balancer import balancer
from dnrm.balancer import manager
from dnrm.openstack.common.fixture import mockpatch
from dnrm.resources import base as resources
from dnrm import tasks
from dnrm.tests import base

CONF = cfg.CONF


class FakeBalancer(mock.Mock):
    pass


class DNRMBalancersManagerTestCase(base.BaseTestCase):
    def setUp(self):
        super(DNRMBalancersManagerTestCase, self).setUp()

        CONF.set_override('balancer', 'dnrm.tests.unit.test_balancer.'
                                      'FakeBalancer')

        self.pool = mock.Mock()
        self.unused_set = mock.Mock()

        self.balancers_manager = manager.DNRMBalancersManager('empty-queue')

    def test_add_balancer(self):
        bal = self.balancers_manager.add_balancer(self.pool,
                                                  self.unused_set, 10, 20)
        self.assertIsInstance(bal, FakeBalancer)

    def test_add_dublicate_balancer(self):
        self.balancers_manager.add_balancer(self.pool, self.unused_set, 10, 20)
        self.assertRaises(ValueError, self.balancers_manager.add_balancer,
                          self.pool, self.unused_set, 10, 20)


class DNRMBalancerTestCase(base.BaseTestCase):
    def setUp(self):
        super(DNRMBalancerTestCase, self).setUp()
        self.pool = mock.Mock()
        self.pool.name = 'fake-pool'
        self.unused_set = mock.Mock()
        self.queue = mock.Mock()

        self.db = self.useFixture(mockpatch.Patch('dnrm.balancer.balancer.'
                                                  'db')).mock

        self.balancer = balancer.DNRMBalancer(self.pool, self.unused_set, 10,
                                              20, self.queue)

    def test_to_str(self):
        self.assertEqual(self.pool.name, str(self.balancer))

    def test_list_resources(self):
        self.balancer.list_resources('status')
        self.unused_set.list.assert_called_once_with('status', None)

    def test_get_resources(self):
        self.balancer.get_resources('status')
        self.unused_set.get.assert_called_once_with('status', None)

    def test_push_resources(self):
        self.balancer.push_resources([{'id': 1, 'type': 'fake-resource-type'},
                                      {'id': 2, 'type': 'fake-resource-type'}])
        self.pool.push.assert_has_calls([mock.call(1), mock.call(2)])

    def test_pop_resources(self):
        self.balancer.pop_resources()
        self.pool.pop.assert_called_once_with(None)

    def test_start(self):
        resource = {'id': 'fake-resource-id', 'type': 'fake-resource-type',
                    'status': resources.STATE_STOPPED}
        self.db.resource_update.return_value = \
            {'status': resources.STATE_STARTED}
        self.balancer.start(resource)
        self.db.resource_update.assert_called_once_with(
            'fake-resource-id', {'status': resources.STATE_STARTED})
        task = self.queue.push.call_args[0][0]
        self.assertIsInstance(task, tasks.StartTask)
        self.assertDictEqual(
            {'id': 'fake-resource-id', 'type': 'fake-resource-type',
             'status': resources.STATE_STARTED}, task._resource)

    def test_stop(self):
        resource = {'id': 'fake-resource-id', 'type': 'fake-resource-type',
                    'status': resources.STATE_STARTED}
        self.db.resource_update.return_value = \
            {'type': 'fake-resource-type', 'status': resources.STATE_STOPPED}
        self.balancer.stop(resource)
        self.db.resource_update.assert_called_once_with(
            'fake-resource-id', {'status': resources.STATE_STOPPED})
        task = self.queue.push.call_args[0][0]
        self.assertIsInstance(task, tasks.StopTask)
        self.assertDictEqual(
            {'id': 'fake-resource-id', 'type': 'fake-resource-type',
             'status': resources.STATE_STOPPED}, task._resource)

    def test_stop_unused(self):
        res = [{'id': 'fake-resource-id-1', 'type': 'fake-resource-type',
                'status': resources.STATE_STARTED},
               {'id': 'fake-resource-id-2', 'type': 'fake-resource-type',
                'status': resources.STATE_STARTED}]
        self.unused_set.list.return_value = res
        self.balancer.stop_unused()
        self.assertEqual(2, self.queue.push.call_count)

    def test_eliminate_deficit(self):
        res1 = [{'id': 'fake-resource-id-1', 'type': 'fake-resource-type',
                 'status': resources.STATE_STARTED},
                {'id': 'fake-resource-id-2', 'type': 'fake-resource-type',
                 'status': resources.STATE_STARTED}]
        res2 = [{'id': 'fake-resource-id-3', 'type': 'fake-resource-type',
                 'status': resources.STATE_STARTED},
                {'id': 'fake-resource-id-4', 'type': 'fake-resource-type',
                 'status': resources.STATE_STARTED}]
        self.unused_set.get.side_effect = [res1, res2]
        self.unused_set.list.return_value = res1
        self.balancer.eliminate_deficit(4)
        self.assertEqual(2, self.queue.push.call_count)
        self.pool.push.assert_has_calls([mock.call(r['id']) for r in res1])

    def test_eliminate_overflow(self):
        self.pool.pop.return_value = [
            {'id': 'fake-resource-id-1', 'type': 'fake-resource-type',
             'status': resources.STATE_STARTED},
            {'id': 'fake-resource-id-2', 'type': 'fake-resource-type',
             'status': resources.STATE_STARTED}]
        self.balancer.eliminate_overflow(2)
        self.pool.pop.assert_called_once_with(2)
        self.assertEqual(2, self.queue.push.call_count)

    def test_balance_deficit(self):
        self.pool.count.return_value = 0
        self.unused_set.count.return_value = 0
        deficit = self.useFixture(
            mockpatch.PatchObject(self.balancer, 'eliminate_deficit')).mock
        overflow = self.useFixture(
            mockpatch.PatchObject(self.balancer, 'eliminate_overflow')).mock
        self.useFixture(mockpatch.PatchObject(self.balancer,
                                              'stop_unused'))
        self.balancer.balance()
        deficit.asserd_called_once_with(10)
        self.assertEqual(0, overflow.call_count)

    def test_balance_overflow(self):
        self.pool.count.return_value = 30
        self.unused_set.count.return_value = 5
        deficit = self.useFixture(
            mockpatch.PatchObject(self.balancer, 'eliminate_deficit')).mock
        overflow = self.useFixture(
            mockpatch.PatchObject(self.balancer, 'eliminate_overflow')).mock
        self.useFixture(mockpatch.PatchObject(self.balancer, 'stop_unused'))
        self.balancer.balance()
        overflow.asserd_called_once_with(10)
        self.assertEqual(0, deficit.call_count)

    def test_balance(self):
        self.pool.count.return_value = 10
        self.unused_set.count.return_value = 5
        deficit = self.useFixture(
            mockpatch.PatchObject(self.balancer, 'eliminate_deficit')).mock
        overflow = self.useFixture(
            mockpatch.PatchObject(self.balancer, 'eliminate_overflow')).mock
        stop_unused = self.useFixture(
            mockpatch.PatchObject(self.balancer, 'stop_unused')).mock
        self.balancer.balance()
        self.assertEqual(0, overflow.call_count)
        self.assertEqual(0, deficit.call_count)
        self.assertEqual(1, stop_unused.call_count)
