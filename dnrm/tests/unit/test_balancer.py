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

from dnrm.balancer import balancer
from dnrm.balancer import manager
from dnrm.resources import base as resources
from dnrm.tests import base


class FakePool:
    name = 'fake_pool_name'

    def push(self, item):
        pass

    def pop(self, n):
        pass

    def get_count(self):
        pass


class FakeUnusedSet:
    def get(self, count, state):
        pass


class FakeQueue:
    def push(self, task):
        pass


class BalancerTestCase(base.BaseTestCase):
    LOW_WATERMARK = 10
    HIGH_WATERMARK = 20

    def setUp(self):
        super(BalancerTestCase, self).setUp()

        self.pool = FakePool()
        self.unused_set = FakeUnusedSet()

        # Mock abstract methods
        with mock.patch.object(balancer.Balancer, 'start'), \
            mock.patch.object(balancer.Balancer, 'stop'), \
            mock.patch.object(balancer.Balancer, 'balance'):

            self.balancer = balancer.Balancer(self.pool,
                                              self.unused_set,
                                              self.LOW_WATERMARK,
                                              self.HIGH_WATERMARK)

    def tearDown(self):
        del self.pool
        del self.unused_set
        del self.balancer
        super(BalancerTestCase, self).tearDown()

    def test_push_resources_into_pool(self):
        """Push resources into pool."""
        with mock.patch.object(self.pool, 'push') as push:
            resources_list = ['resource1', 'resource2']

            push_calls = [mock.call('resource1'),
                          mock.call('resource2')]

            self.balancer.push_resources_into_pool(resources_list)

            self.assertEqual(push_calls,
                             push.mock_calls)

    def test_get_current_pool_size(self):
        with mock.patch.object(self.pool, 'get_count') as get_count:
            get_count.return_value = 20
            self.assertEqual(self.balancer.get_current_pool_size(),
                             20)
            get_count.assert_called_once_with()

    def test_get_stopped_resources(self):
        with mock.patch.object(self.unused_set, 'get') as stopped_list:
            stopped_list.return_value = ['resource1', 'resource2']
            self.assertEqual(self.balancer.get_stopped_resources(2),
                             ['resource1', 'resource2'])
            stopped_list.assert_called_once_with(resources.STATE_STOPPED, 2)

    def test_get_started_resources(self):
        with mock.patch.object(self.unused_set, 'get') as started_list:
            started_list.return_value = ['resource1', 'resource2']
            self.assertEqual(self.balancer.get_started_resources(2),
                             ['resource1', 'resource2'])
            started_list.assert_called_once_with(resources.STATE_STARTED, 2)

    def test_pop_resources_from_pool(self):
        with mock.patch.object(self.pool, 'pop') as pop:
            pop.return_value = ['resource1', 'resource2']
            self.assertEqual(self.balancer.pop_resources_from_pool(2),
                             ['resource1', 'resource2'])
            pop.assert_called_once_with(2)


class TaskBasedBalancerTestCase(base.BaseTestCase):
    LOW_WATERMARK = 10
    HIGH_WATERMARK = 20

    def setUp(self):
        super(TaskBasedBalancerTestCase, self).setUp()

        self.pool = FakePool()
        self.unused_set = FakeUnusedSet()
        self.queue = FakeQueue()

        # Mock abstract methods
        with mock.patch.object(balancer.TaskBasedBalancer, 'balance'):
            self.balancer = balancer.TaskBasedBalancer(self.pool,
                                                       self.unused_set,
                                                       self.LOW_WATERMARK,
                                                       self.HIGH_WATERMARK,
                                                       self.queue)

    def tearDown(self):
        del self.pool
        del self.unused_set
        del self.balancer
        super(TaskBasedBalancerTestCase, self).tearDown()

    def test_start(self):
        with mock.patch('dnrm.tasks.StartTask') as StartTask, \
            mock.patch.object(self.queue, 'push') as push:

            task = 'task'
            resource = 'resource'

            StartTask.return_value = task

            self.balancer.start(resource)

            StartTask.assert_called_once_with(resource)
            push.assert_called_once_with(task)

    def test_stop(self):
        with mock.patch('dnrm.tasks.StopTask') as StopTask, \
            mock.patch.object(self.queue, 'push') as push:

            task = 'task'
            resource = 'resource'

            StopTask.return_value = task

            self.balancer.stop(resource)

            StopTask.assert_called_once_with(resource)
            push.assert_called_once_with(task)


class SimpleBalancerTestCase(base.BaseTestCase):
    LOW_WATERMARK = 10
    HIGH_WATERMARK = 20

    def generate_started_resources(self, *resources):
        resources = list(resources)

        def get_started_resources(n=None):
            if n is None:
                n = len(resources)
            r = []
            while n > 0:
                if not resources:
                    break
                r.append(resources.pop(0))
                n -= 1
            return r

        return get_started_resources

    def generate_stopped_resources(self, *resources):
        resources = list(resources)

        def get_stopped_resources(deficit):
            r = []
            while deficit > 0:
                if not resources:
                    break
                r.append(resources.pop(0))
                deficit -= 1
            return r

        return get_stopped_resources

    def generate_pool_sizes(self, *pool_sizes):
        pool_sizes = list(pool_sizes)

        def get_current_pool_size():
            return pool_sizes.pop(0)

        return get_current_pool_size

    def setUp(self):
        super(SimpleBalancerTestCase, self).setUp()
        self.pool = FakePool()
        self.unused_set = FakeUnusedSet()

        self.balancer = balancer.SimpleBalancer(self.pool,
                                                self.unused_set,
                                                self.LOW_WATERMARK,
                                                self.HIGH_WATERMARK)

    def tearDown(self):
        del self.balancer
        del self.pool
        del self.unused_set
        super(SimpleBalancerTestCase, self).tearDown()

    def test_balance_push_started(self):
        with mock.patch.object(self.balancer,
                               'get_current_pool_size') \
            as get_current_pool_size, \
            mock.patch.object(self.balancer,
                              'get_started_resources') \
            as get_started_resources, \
            mock.patch.object(self.balancer,
                              'push_resources_into_pool') \
            as push_resources_into_pool:

            get_started_resources_calls = [
                mock.call(self.HIGH_WATERMARK - self.LOW_WATERMARK),
                mock.call()]

            # Generate initial pool size (self.LOW_WATERMARK) and
            # pool size after push started resource into pool (+2)
            get_current_pool_size.side_effect = (
                self.generate_pool_sizes(self.LOW_WATERMARK,
                                         self.LOW_WATERMARK + 2,
                                         self.LOW_WATERMARK + 2))

            get_started_resources.side_effect = (
                self.generate_started_resources('resource1',
                                                'resource2'))

            self.balancer.balance()

            push_resources_into_pool.assert_called_once_with([
                'resource1',
                'resource2'])

            self.assertEqual(get_started_resources_calls,
                             get_started_resources.mock_calls)

    def test_balance_eliminate_deficit(self):
        deficit = 2
        initial_pool_size = self.LOW_WATERMARK - deficit

        with mock.patch.object(self.balancer,
                               'get_current_pool_size') \
            as get_current_pool_size, \
            mock.patch.object(self.balancer,
                              'get_started_resources') \
            as get_started_resources, \
            mock.patch.object(self.balancer,
                              'eliminate_deficit') \
            as eliminate_deficit:

            get_started_resources_calls = [
                mock.call(self.HIGH_WATERMARK - initial_pool_size),
                mock.call()]

            get_current_pool_size.side_effect = (
                self.generate_pool_sizes(initial_pool_size,
                                         initial_pool_size,
                                         initial_pool_size))

            # No started resources.
            get_started_resources.side_effect = (
                self.generate_started_resources())

            self.balancer.balance()

            eliminate_deficit.assert_called_once_with(deficit)

            self.assertEqual(get_started_resources_calls,
                             get_started_resources.mock_calls)

    def test_balance_eliminate_overflow(self):
        overflow = 2
        initial_pool_size = self.HIGH_WATERMARK + overflow

        with mock.patch.object(self.balancer,
                               'get_current_pool_size') \
            as get_current_pool_size, \
            mock.patch.object(self.balancer,
                              'get_started_resources') \
            as get_started_resources, \
            mock.patch.object(self.balancer,
                              'eliminate_overflow') \
            as eliminate_overflow:

            get_started_resources_calls = [mock.call()]

            get_current_pool_size.side_effect = (
                self.generate_pool_sizes(initial_pool_size,
                                         initial_pool_size,
                                         initial_pool_size))

            # No started resources.
            get_started_resources.side_effect = (
                self.generate_started_resources())

            self.balancer.balance()

            eliminate_overflow.assert_called_once_with(overflow)

            self.assertEqual(get_started_resources_calls,
                             get_started_resources.mock_calls)

    def test_eliminate_deficit(self):
        deficit = 2

        with mock.patch.object(self.balancer,
                               'get_stopped_resources') \
            as get_stopped_resources, \
            mock.patch.object(self.balancer,
                              'start') \
            as start:

            stopped_resources = ['stopped_resource1',
                                 'stopped_resource2']

            get_stopped_resources.side_effect = (
                self.generate_stopped_resources(*stopped_resources))

            start_calls = [mock.call('stopped_resource1'),
                           mock.call('stopped_resource2')]

            self.balancer.eliminate_deficit(deficit)

            get_stopped_resources.assert_called_once_with(deficit)

            self.assertEqual(start_calls,
                             start.mock_calls)

    def test_eliminate_overflow(self):
        overflow = 2

        with mock.patch.object(self.pool, 'pop') as pop, \
            mock.patch.object(self.balancer, 'stop') as stop:

            pool = ['resource1',
                    'resource2']
            pop.return_value = pool

            stop_calls = [mock.call('resource1'),
                          mock.call('resource2')]

            self.balancer.eliminate_overflow(overflow)

            pop.assert_called_once_with(overflow)

            self.assertEqual(stop_calls,
                             stop.mock_calls)


class BalancersManagerTestCase(base.BaseTestCase):
    def setUp(self):
        super(BalancersManagerTestCase, self).setUp()
        self.balancers_manager = manager.DNRMBalancersManager('empty-queue')

    def tearDown(self):
        del self.balancers_manager
        super(BalancersManagerTestCase, self).tearDown()

    def test_add_balancer(self):
        balancer = 'balancer'
        pool = FakePool()
        unused_set = 'unused set'
        low_watermark = 1
        high_watermark = 2

        with mock.patch.object(self.balancers_manager, 'create_balancer') \
            as create_balancer:

            create_balancer.return_value = balancer

            created_balancer = self.balancers_manager.add_balancer(
                pool, unused_set,
                low_watermark, high_watermark)

            self.assertEqual(created_balancer, balancer)
            self.assertEqual(len(self.balancers_manager.balancers), 1)
            self.assertEqual(self.balancers_manager.balancers[pool.name],
                             balancer)

    def test_add_duplicate_balancer(self):
        pool = FakePool()
        unused_set = 'unused_set'
        low_watermark = 1
        high_watermark = 1

        with mock.patch.object(self.balancers_manager,
                               'balancer_already_added') \
            as balancer_already_added:

            balancer_already_added.return_value = True

            self.assertRaises(ValueError,
                              self.balancers_manager.add_balancer,
                              pool,
                              unused_set,
                              low_watermark,
                              high_watermark)

            balancer_already_added.assert_called_once_with(pool.name)
