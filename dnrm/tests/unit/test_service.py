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
from oslo.config import cfg

from dnrm.exceptions import wsgi as wsgi_exc
from dnrm import service
from dnrm.tests import base


APP_NAME = "test"
APPLICATION = "app_test"

TEST_PORT = '2060'
TEST_HOST = '8.8.8.8'


class TestWSGIServiceTestCase(base.BaseTestCase):

    def setUp(self):
        super(TestWSGIServiceTestCase, self).setUp()
        cfg.CONF.set_override('bind_port', TEST_PORT)
        cfg.CONF.set_override('bind_host', TEST_HOST)
        with mock.patch.object(cfg.CONF, 'log_opt_values'):
            self.wsgi_service = service.WsgiService(app_name=APP_NAME)

    def test_start(self):
        calls_load_paste_app_func = [mock.call(APP_NAME)]
        calls_server_class = [mock.call(APP_NAME),
                              mock.call().start(APPLICATION,
                                                TEST_PORT,
                                                TEST_HOST)]

        with mock.patch('dnrm.common.config.load_paste_app',
                        return_value=APPLICATION) as lap:
            with mock.patch('dnrm.wsgi.Server') as server:
                with mock.patch.object(cfg.CONF, 'log_opt_values'):

                    self.assertEqual(self.wsgi_service.start(),
                                     self.wsgi_service)
                    self.assertTrue(calls_load_paste_app_func, lap.mock_calls)
                    self.assertTrue(calls_server_class, server.mock_calls)

    def test_start_rases_no_known_applications(self):
        with mock.patch('dnrm.common.config.load_paste_app',
                        return_value=None):

            self.assertRaises(wsgi_exc.NoKnownApplications,
                              self.wsgi_service.start)
