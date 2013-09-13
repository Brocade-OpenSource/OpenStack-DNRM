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

from mock import patch

from dnrm.api import collections
from dnrm.api import drivers
from dnrm.api import resources
from dnrm.api import router
from dnrm.api import versions
from dnrm.openstack.common.fixture import mockpatch
from dnrm.tests import base
from dnrm.tests.unit.api import fakes

FAKE_RESOURCE_ID = "00000000-0000-0000-0003-000000000001"
FAKE_RESOURCE_TYPE = "fake_resource_type"


class RouterTestCase(base.BaseTestCase):
    def setUp(self):
        super(RouterTestCase, self).setUp()
        self.useFixture(mockpatch.Patch(
            'dnrm.resources.manager.ResourceManager'))
        self.app = router.APIRouter()

    # API Version test case
    def test_version_list(self):
        with patch.object(versions.VersionController, 'index',
                          return_value={}) as mock_method:
            req = fakes.HTTPRequest.blank('/')
            req.method = 'GET'
            req.get_response(self.app)
            self.assertTrue(mock_method.called)

    # Collections test case
    def test_collection_list(self):
        with patch.object(collections.CollectionController, 'index',
                          return_value={}) as mock_method:
            req = fakes.HTTPRequest.blank('/v1/')
            req.method = 'GET'
            req.get_response(self.app)
            self.assertTrue(mock_method.called)

    # Resources test case
    def test_resources_list(self):
        with patch.object(resources.ResourceController, 'index',
                          return_value={}) as mock_method:
            req = fakes.HTTPRequest.blank('/v1/resources/')
            req.method = 'GET'
            req.get_response(self.app)
            self.assertTrue(mock_method.called)

    def test_resource_get(self):
        with patch.object(resources.ResourceController, 'show',
                          return_value={}) as mock_method:
            url = '/v1/resources/%s' % FAKE_RESOURCE_ID
            req = fakes.HTTPRequest.blank(url)
            req.method = 'GET'
            req.get_response(self.app)
            self.assertTrue(mock_method.called)

    def test_resource_create(self):
        with patch.object(resources.ResourceController, 'create',
                          return_value={}) as mock_method:
            req = fakes.HTTPRequest.blank('/v1/resources/')
            req.method = 'POST'
            body = {"resource": {"resource_type": FAKE_RESOURCE_TYPE}}
            req.body = json.dumps(body)
            req.get_response(self.app)
            self.assertTrue(mock_method.called)

    def test_resource_update(self):
        with patch.object(resources.ResourceController, 'update',
                          return_value={}) as mock_method:
            url = '/v1/resources/%s' % FAKE_RESOURCE_ID
            req = fakes.HTTPRequest.blank(url)
            req.method = 'PUT'
            body = {"resource": {"description": "fake_description"}}
            req.body = json.dumps(body)
            req.get_response(self.app)
            self.assertTrue(mock_method.called)

    def test_resource_delete(self):
        with patch.object(resources.ResourceController, 'delete',
                          return_value={}) as mock_method:
            url = '/v1/resources/%s' % FAKE_RESOURCE_ID
            req = fakes.HTTPRequest.blank(url)
            req.method = 'DELETE'
            req.get_response(self.app)
            self.assertTrue(mock_method.called)

    # Drivers test case
    def test_drivers_list(self):
        with patch.object(drivers.DriverController, 'index',
                          return_value={}) as mock_method:
            req = fakes.HTTPRequest.blank('/v1/drivers/')
            req.method = 'GET'
            req.get_response(self.app)
            self.assertTrue(mock_method.called)

    def test_driver_get(self):
        with patch.object(drivers.DriverController, 'show',
                          return_value={}) as mock_method:
            url = '/v1/drivers/%s' % FAKE_RESOURCE_TYPE
            req = fakes.HTTPRequest.blank(url)
            req.method = 'GET'
            req.get_response(self.app)
            self.assertTrue(mock_method.called)
