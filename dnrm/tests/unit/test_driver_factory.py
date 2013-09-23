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

from dnrm.drivers import base as driver_base
from dnrm.drivers import factory
from dnrm.tests import base


class TestDriver(driver_base.DriverBase):
    def init(self, resource):
        pass

    def stop(self, resource):
        pass

    def wipe(self, resource):
        pass

    def check(self, resource):
        pass

    def validate_resource(self, resource):
        pass

    def schema(self):
        pass

    def prepare_resource(self, state):
        pass


class DriverFactoryTestCase(base.BaseTestCase):
    """ResourceFactory test case."""

    def setUp(self):
        self.import_class = self._mock(
            'dnrm.openstack.common.importutils.import_class',
            retval=TestDriver)
        self.get_drivers_names = self._mock(
            'dnrm.common.config.get_drivers_names', retval=['foo.bar.test'])

        super(DriverFactoryTestCase, self).setUp()

    @property
    def factory(self):
        return factory.DriverFactory()

    def _mock(self, function, retval=None, side_effect=None):
        patcher = mock.patch(function)
        self.addCleanup(patcher.stop)
        mock_object = patcher.start()
        if retval is not None:
            mock_object.return_value = retval
        if side_effect is not None:
            mock_object.side_effect = side_effect
        return mock_object

    def test_get(self):
        self.assertTrue(isinstance(self.factory.get('foo.bar.test'),
                                   TestDriver))
        self.get_drivers_names.assert_called_once_with()
        self.import_class.assert_called_once_with('foo.bar.test')
