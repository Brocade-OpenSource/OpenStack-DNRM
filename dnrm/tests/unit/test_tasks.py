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
from dnrm.resources import base as resources
from dnrm import tasks
from dnrm.tests import base


class TasksTestCase(base.BaseTestCase):
    def setUp(self):
        self.config(task_queue_timeout=1)
        self.factory_cls = self._mock('dnrm.drivers.factory.DriverFactory')
        self.factory = self.factory_cls.return_value
        self.driver = self.factory.get.return_value
        super(TasksTestCase, self).setUp()

    def _mock(self, function, retval=None, side_effect=None):
        patcher = mock.patch(function)
        self.addCleanup(patcher.stop)
        mock_object = patcher.start()
        if retval is not None:
            mock_object.return_value = retval
        if side_effect is not None:
            mock_object.side_effect = side_effect
        return mock_object

    def _make_resource(self):
        return dict(status=resources.STATE_STOPPED, klass='foobar',
                    type='fake-driver')

    def test_start_task(self):
        resource = self._make_resource()
        task = tasks.StartTask(resource)
        self.assertEquals(resource, task.execute(self.factory))
        self.factory.get.assert_called_once_with('fake-driver')
        self.driver.init.assert_called_once_with(resource)

    def test_stop_task(self):
        resource = self._make_resource()
        task = tasks.StopTask(resource)
        self.assertEquals(resource, task.execute(self.factory))
        self.factory.get.assert_called_once_with('fake-driver')
        self.driver.stop.assert_called_once_with(resource)

    def test_wipe_task(self):
        resource = self._make_resource()
        task = tasks.WipeTask(resource)
        self.assertEquals(resource, task.execute(self.factory))
        self.factory.get.assert_called_once_with('fake-driver')
        self.driver.wipe.assert_called_once_with(resource)

    def test_delete_task(self):
        resource = self._make_resource()
        task = tasks.DeleteTask(resource)
        self.assertEquals(resource, task.execute(self.factory))
        self.factory.get.assert_called_once_with('fake-driver')
        self.driver.stop.assert_called_once_with(resource)
