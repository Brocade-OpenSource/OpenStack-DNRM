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
from dnrm.openstack.common.fixture import mockpatch
from dnrm.tests import base


class TestDriver1(driver_base.DriverBase):
    resource_class = 'L3'

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


class TestDriver2(TestDriver1):
    resource_class = 'L3'


class DriverFactoryTestCase(base.BaseTestCase):
    """ResourceFactory test case."""

    def setUp(self):
        super(DriverFactoryTestCase, self).setUp()
        self.import_class = self.useFixture(mockpatch.Patch(
            'dnrm.openstack.common.importutils.import_class',
            side_effect=[TestDriver1, TestDriver2])).mock
        self.get_drivers_names = self.useFixture(mockpatch.Patch(
            'dnrm.common.config.get_drivers_names',
            return_value=['foo.bar.test1', 'foo.bar.test2'])).mock
        self.factory = factory.DriverFactory()

    def test_get(self):
        self.assertIsInstance(self.factory.get('foo.bar.test1'), TestDriver1)
        self.get_drivers_names.assert_called_once_with()
        self.import_class.assert_has_calls([mock.call('foo.bar.test1'),
                                            mock.call('foo.bar.test2')])

    def test_get_names_all(self):
        drivers = self.factory.get_names('L3')
        self.assertEqual(2, len(drivers))

    def test_get_names_null(self):
        drivers = self.factory.get_names('L2')
        self.assertEqual(0, len(drivers))
