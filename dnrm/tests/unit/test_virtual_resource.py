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
from dnrm import exceptions
from dnrm.resources import base as resources
from dnrm.resources import factory
from dnrm.resources import virtual_resource
from dnrm.tests import base


class VirtualResourceTestCase(base.BaseTestCase):
    """ResourceFactory test case."""

    @property
    def factory(self):
        return factory.ResourceFactory()

    def test_get(self):
        self.assertEquals(virtual_resource.VirtualResource,
                          self.factory.get_class('nova_vm'))

    def test_import_error(self):
        self.assertIn(virtual_resource.VirtualResource,
                      self.factory.list_classes())

    def test_create_default(self):
        res = self.factory.create('nova_vm', resources.STATE_STOPPED)
        self.assertIsNotNone(res)

    def test_create_non_default(self):
        res = self.factory.create('nova_vm', resources.STATE_STOPPED,
                                  {'address': '10.0.0.2',
                                   'instance_id': 'fake-instance-id'})
        self.assertIsNotNone(res)

    def test_create_not_valid(self):
        self.assertRaises(exceptions.InvalidResource, self.factory.create,
                          'nova_vm', resources.STATE_STOPPED, {})

    def test_create_started(self):
        self.assertRaises(NotImplementedError, self.factory.create,
                          'nova_vm', resources.STATE_STARTED)
