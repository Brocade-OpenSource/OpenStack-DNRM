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

from dnrm.api import drivers
from dnrm.common import config
from dnrm.openstack.common.fixture import mockpatch
from dnrm.openstack.common import log as logging
from dnrm.tests import base
from dnrm.tests.unit.api import fakes


FAKE_DRIVER_TYPE = "com.router.brocade.vyatta.6000"
LOG = logging.getLogger(__name__)


class DriverApiTest(base.DBBaseTestCase):
    def setUp(self):
        super(DriverApiTest, self).setUp()
        self.manager = mock.Mock()
        self.useFixture(mockpatch.Patch(
            'dnrm.resources.manager.ResourceManager',
            return_value=self.manager))

        self.controller = drivers.DriverController()

    def test_drivers_name_list(self):
        with mock.patch.object(config, 'get_drivers_names',
                               return_value=[FAKE_DRIVER_TYPE]):
            req = fakes.HTTPRequest.blank('/v1/drivers/')
            req.method = 'GET'
            driver_names = self.controller.index(req)
            self.assertTrue(driver_names, [FAKE_DRIVER_TYPE])

    def test_driver_get_schema(self):
        url = '/v1/drivers/%s' % FAKE_DRIVER_TYPE
        req = fakes.HTTPRequest.blank(url)
        req.method = 'GET'
        self.controller.show(req, FAKE_DRIVER_TYPE)
        self.manager.schema.assert_called_with(None, FAKE_DRIVER_TYPE)
