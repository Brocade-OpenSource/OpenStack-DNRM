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
import json
import mock

from dnrm.api import resources
from dnrm.openstack.common.fixture import mockpatch
from dnrm.openstack.common import log as logging
from dnrm.tests import base
from dnrm.tests.unit.api import fakes

LOG = logging.getLogger(__name__)

FAKE_RESOURCE_ID = "00000000-0000-0000-0003-000000000001"
FAKE_RESOURCE_TYPE = "fake_resource_type"


class ResourceApiTest(base.DBBaseTestCase):
    def setUp(self):
        super(ResourceApiTest, self).setUp()
        self.manager = mock.Mock()
        self.useFixture(mockpatch.Patch(
            'dnrm.resources.manager.ResourceManager',
            return_value=self.manager))

        self.controller = resources.ResourceController()

    def test_resources_list(self):
        req = fakes.HTTPRequest.blank('/v1/resources/')
        self.controller.index(req)
        self.manager.list.assert_called_with(None, {})

    def test_resource_add(self):
        req = fakes.HTTPRequest.blank('/v1/resources/')
        req.method = 'POST'
        body = {"resource": {"resource_type": FAKE_RESOURCE_TYPE}}
        req.body = json.dumps(body)
        self.controller.create(req, body)
        self.manager.add.assert_called_with(None, FAKE_RESOURCE_TYPE,
                                            body['resource'])

    def test_resource_get(self):
        url = '/v1/resources/%s' % FAKE_RESOURCE_ID
        req = fakes.HTTPRequest.blank(url)
        req.method = 'GET'
        self.controller.show(req, FAKE_RESOURCE_ID)
        self.manager.get.assert_called_with(None, FAKE_RESOURCE_ID)

    def test_resource_allocate(self):
        url = '/v1/resources/%s' % FAKE_RESOURCE_ID
        req = fakes.HTTPRequest.blank(url)
        req.method = 'PUT'
        body = {"resource": {"allocated": True}}
        req.body = json.dumps(body)
        self.manager.get.return_value = {'id': FAKE_RESOURCE_ID}
        self.controller.update(req, FAKE_RESOURCE_ID, body)
        self.manager.allocate.assert_called_with(None, FAKE_RESOURCE_ID)

    def test_resource_deallocate(self):
        url = '/v1/resources/%s' % FAKE_RESOURCE_ID
        req = fakes.HTTPRequest.blank(url)
        req.method = 'PUT'
        body = {"resource": {"allocated": False}}
        req.body = json.dumps(body)
        self.manager.get.return_value = {'id': FAKE_RESOURCE_ID}
        self.controller.update(req, FAKE_RESOURCE_ID, body)
        self.manager.deallocate.assert_called_with(None, FAKE_RESOURCE_ID)

    def test_resource_delete(self):
        url = '/v1/resources/%s' % FAKE_RESOURCE_ID
        req = fakes.HTTPRequest.blank(url)
        req.method = 'DELETE'
        self.manager.get.return_value = {'id': FAKE_RESOURCE_ID}
        self.controller.delete(req, FAKE_RESOURCE_ID)
        self.manager.delete.assert_called_with(None, FAKE_RESOURCE_ID, False)
