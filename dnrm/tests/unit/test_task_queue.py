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

import dnrm.common.config  # noqa
from dnrm.db import api as db_api
from dnrm.resources import base as resource_base
from dnrm import task_queue
from dnrm import tasks
from dnrm.tests import base

from eventlet import greenthread
from eventlet import queue


class TestTask(tasks.Task):
    def __init__(self, process_state=resource_base.STATE_ERROR,
                 success_state=resource_base.STATE_ERROR,
                 fail_state=resource_base.STATE_ERROR,
                 in_states=(resource_base.STATE_ERROR,)):
        self.in_states = in_states
        self.process_state = process_state
        self.success_state = success_state
        self.fail_state = fail_state
        res = dict(id='fake-id', status=resource_base.STATE_STOPPED, foo='bar')
        super(TestTask, self).__init__(res)

    def execute(self):
        return self._resource


class MockedEventletTestCase(base.BaseTestCase):
    def setUp(self):
        self.config(task_queue_timeout=1)
        self.light_queue_cls = self._mock('eventlet.queue.LightQueue')
        self.light_queue = self.light_queue_cls.return_value
        self.task_queue = task_queue.TaskQueue()
        self.driver_factory = mock.MagicMock()
        self.worker = task_queue.QueuedTaskWorker(self.task_queue,
                                                  self.driver_factory)
        self.db = self._mock('dnrm.db.api.resource_update')
        super(MockedEventletTestCase, self).setUp()

    def _mock(self, function, retval=None, side_effect=None):
        patcher = mock.patch(function)
        self.addCleanup(patcher.stop)
        mock_object = patcher.start()
        if retval is not None:
            mock_object.return_value = retval
        if side_effect is not None:
            mock_object.side_effect = side_effect
        return mock_object


class TaskQueueTestCase(MockedEventletTestCase):
    """TaskQueue test case."""
    def setUp(self):
        self.old_impl = db_api.IMPL
        db_api.IMPL = mock.MagicMock()
        self.db = db_api.IMPL
        super(TaskQueueTestCase, self).setUp()

    def tearDown(self):
        super(TaskQueueTestCase, self).tearDown()
        db_api.IMPL = self.old_impl

    def test_push(self):
        task = TestTask()
        self.task_queue.push(task)
        self.light_queue.put.assert_called_once_with(task)

    def test_pop(self):
        task = TestTask()
        self.light_queue.get.return_value = task
        self.assertEquals(task, self.task_queue.pop(timeout=31337))
        self.light_queue.get.assert_called_once_with(block=True, timeout=31337)

    def test_pop_empty(self):
        self.light_queue.get.side_effect = queue.Empty
        self.assertIsNone(self.task_queue.pop(block=False))
        self.light_queue.get.assert_called_once_with(block=False, timeout=None)


class QueuedTaskWorkerTestCase(base.BaseTestCase):
    """QueuedTaskWorker test case."""

    def setUp(self):
        self.resource_update = self._mock('dnrm.db.api.resource_update')
        self.config(task_queue_timeout=1)
        self.task_queue = task_queue.TaskQueue()
        self.driver_factory = mock.MagicMock()
        self.worker = task_queue.QueuedTaskWorker(self.task_queue,
                                                  self.driver_factory)
        self.old_impl = db_api.IMPL
        db_api.IMPL = mock.MagicMock()
        self.db = db_api.IMPL
        super(QueuedTaskWorkerTestCase, self).setUp()

    def tearDown(self):
        super(QueuedTaskWorkerTestCase, self).tearDown()
        db_api.IMPL = self.old_impl

    def _mock(self, function, retval=None, side_effect=None):
        patcher = mock.patch(function)
        self.addCleanup(patcher.stop)
        mock_object = patcher.start()
        if retval is not None:
            mock_object.return_value = retval
        if side_effect is not None:
            mock_object.side_effect = side_effect
        return mock_object

    def test_start(self):
        task = mock.MagicMock()
        task.get_resource_id.return_value = 'fake-id'
        task.process_state = resource_base.STATE_STARTING
        task.in_states = (resource_base.STATE_ERROR,)
        self.db.resource_compare_update.return_value = 1
        resource = {'id': 'fake-id'}
        task.execute.return_value = resource
        self.task_queue.push(task)
        self.worker.start()
        greenthread.sleep()
        task.execute.assert_called_once(self.driver_factory)
        self.db.resource_compare_update.assert_called_once_with(
            'fake-id', {'status': (resource_base.STATE_ERROR,)},
            {'status': resource_base.STATE_STARTING, 'processing': True})

    def test_execute_exception(self):
        task = mock.MagicMock()
        task.in_states = (resource_base.STATE_ERROR,)
        task.get_resource_id.return_value = 'fake-id'
        task.execute.side_effect = RuntimeError('fake-exception for test')
        self.db.resource_compare_update.return_value = 1
        self.task_queue.push(task)
        self.worker.start()
        greenthread.sleep()
        task.execute.assert_called_once(self.driver_factory)
        self.db.resource_compare_update.assert_called_once_with(
            task.get_resource_id(), {'status': (resource_base.STATE_ERROR,)},
            mock.ANY)

    def test_stop(self):
        self.worker.start()
        self.worker.stop()
        self.assertFalse(self.worker._running)
