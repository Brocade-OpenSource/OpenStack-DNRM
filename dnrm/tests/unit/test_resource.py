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
from dnrm.resources import base as resources
from dnrm.tests import base


class TestResource(resources.Resource):
    @classmethod
    def validate(cls, resource_data):
        pass

    @classmethod
    def schema(cls):
        return {}


class ResourceTestCase(base.BaseTestCase):
    """Vyatta vRouter driver test case."""

    def setUp(self):
        super(ResourceTestCase, self).setUp()

    def test_getattr(self):
        resource = TestResource({'something': 1})
        self.assertEquals(1, resource.something)

    def test_setattr(self):
        resource = TestResource()
        resource.something = 1
        self.assertEquals(1, resource._data['something'])

    def test_getattr_raises(self):
        resource = TestResource()
        self.assertRaises(AttributeError, lambda: resource.foobar)

    def test_to_dict(self):
        resource = TestResource()
        resource.id = 'fake-uuid'
        resource.foo = 'bar'
        self.assertEquals({'foo': 'bar', 'state': resources.STATE_STOPPED},
                          resource.to_dict())
        self.assertEquals('fake-uuid', resource.id)
