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

from dnrm import exceptions
from dnrm.resources import base as resources
from dnrm.resources import factory
from dnrm.tests import base


class FakeModule(object):
    def __init__(self, name):
        class FakeResource(resources.Resource):
            type_name = name

            @classmethod
            def validate(self, data):
                if data.get('not_valid'):
                    raise exceptions.InvalidResource()

            @classmethod
            def create(cls, state, data=None):
                return cls(data)
        self.FakeResource = FakeResource
        self.foo = int
        self.bar = 'baz'


class ResourceFactoryTestCase(base.BaseTestCase):
    """ResourceFactory test case."""

    def setUp(self):
        self.module_a = FakeModule('a')
        self.module_b = FakeModule('b')
        self.modules = [self.module_a, self.module_b]

        super(ResourceFactoryTestCase, self).setUp()

    @property
    def factory(self):
        self._mock('glob.glob', retval=['/x/module_a.py', '/x/module_b.py'])
        self._mock('dnrm.openstack.common.importutils.import_module',
                   side_effect=self.modules)

        return factory.ResourceFactory()

    def _mock(self, function, retval=None, side_effect=None):
        patcher = mock.patch(function)
        self.addCleanup(patcher.stop)
        mock_object = patcher.start()
        if retval is not None:
            mock_object.return_value = retval
        if side_effect is not None:
            mock_object.side_effect = side_effect
        return mock_object

    def test_list(self):
        classes = self.factory.list_classes()
        self.assertIn(self.module_a.FakeResource, classes)
        self.assertIn(self.module_b.FakeResource, classes)

    def test_get(self):
        self.assertEquals(self.module_a.FakeResource,
                          self.factory.get_class('a'))

    def test_import_error(self):
        self.modules = [self.module_a, RuntimeError()]
        classes = self.factory.list_classes()
        self.assertIn(self.module_a.FakeResource, classes)
        self.assertNotIn(self.module_b.FakeResource, classes)

    def test_create_default(self):
        res = self.factory.create('a', resources.STATE_STOPPED)
        self.assertIsNotNone(res)

    def test_create_non_default(self):
        res = self.factory.create('a', resources.STATE_STOPPED, {})
        self.assertIsNotNone(res)

    def test_create_not_valid(self):
        self.assertRaises(exceptions.InvalidResource, self.factory.create,
                          'a', resources.STATE_STOPPED, {'not_valid': True})

    def test_create_invalid_name(self):
        self.assertRaises(exceptions.InvalidResourceType, self.factory.create,
                          'foobar', resources.STATE_STOPPED)
