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
import contextlib
import mock
import socket

from dnrm.drivers.vyatta.vrouter_driver import VyattaVRouterDriver
from dnrm import exceptions
from dnrm.resources import base as resources
from dnrm.tests import base
from oslo.config import cfg

CONF = cfg.CONF


def make_resource(instance_id='inst-id', address='10.0.0.1',
                  state=resources.STATE_STARTED):
    res = {'status': state}
    if address is not None:
        res['address'] = address
    if instance_id is not None:
        res['instance_id'] = instance_id
    return res


class VrouterDriverTestCase(base.BaseTestCase):
    """Vyatta vRouter driver test case."""

    def setUp(self):
        CONF.set_override('api_port', 31337, 'VROUTER')
        CONF.set_override('api_public_key', 'public-key', 'VROUTER')
        CONF.set_override('api_private_key', 'private-key', 'VROUTER')
        CONF.set_override('tenant', 'fake-tenant-id', 'VROUTER')
        CONF.set_override('tenant_admin_name', 'admin', 'VROUTER')
        CONF.set_override('tenant_admin_password', 'password', 'VROUTER')
        CONF.set_override('keystone_url', 'http://keystone.com/v2', 'VROUTER')
        CONF.set_override('image_id', 'fake-image-id', 'VROUTER')
        CONF.set_override('flavor', 1234, 'VROUTER')
        CONF.set_override('management_network_id', 'fake-net-id', 'VROUTER')
        CONF.set_override('management_network_cidr', '10.0.0.0/24', 'VROUTER')

        self.driver = VyattaVRouterDriver()
        self.novaclient_cls = self._mock('novaclient.v1_1.client.Client')
        self.novaclient = self.novaclient_cls.return_value
        self.httpconn_cls = self._mock('httplib.HTTPConnection')
        self.httpconn = self.httpconn_cls.return_value

        self.time = self._mock('time.time')
        self.time.return_value = 1
        self.sleep = self._mock('eventlet.greenthread.sleep')

        super(VrouterDriverTestCase, self).setUp()

    def _check_novaclient(self):
        self.novaclient_cls.assert_called_with('admin', 'password', None,
                                               'http://keystone.com/v2',
                                               service_type='compute',
                                               tenant_id='fake-tenant-id')

    @contextlib.contextmanager
    def _check_check_instance(self, address, status=401):
        response = mock.MagicMock()
        response.status = status
        self.httpconn.getresponse.return_value = response
        yield
        if self.httpconn_cls.mock_calls:
            self.httpconn_cls.assert_called_with(address, 31337)

    @contextlib.contextmanager
    def _check_init(self, instance_state='ACTIVE', num_ifaces=1, num_ips=1):
        server = mock.MagicMock()
        server.id = 'inst-id'
        server.status = instance_state
        self.novaclient.servers.create.return_value = server
        self.novaclient.servers.get.return_value = server

        interface = mock.MagicMock()
        fixed_ip = dict(ip_address='10.0.0.1')
        interface.fixed_ips = [fixed_ip] * num_ips
        server.interface_list.return_value = [interface] * num_ifaces

        with self._check_check_instance(fixed_ip['ip_address']):
            yield

        self.novaclient.servers.create.assert_called_once_with(
            mock.ANY, 'fake-image-id', 1234, nics=[{'net-id': 'fake-net-id'}])
        if self.novaclient.servers.get.mock_calls:
            self.novaclient.servers.get.assert_called_with('inst-id')

    def _mock(self, function):
        patcher = mock.patch(function)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def test_resource_stop_resource(self):
        resource = make_resource(instance_id='inst-id')
        self.driver.stop(resource)
        self._check_novaclient()
        self.novaclient.servers.delete.assert_called_once_with('inst-id')

    def test_check(self):
        resource = make_resource(address='10.0.0.1')
        with self._check_check_instance(resource['address']):
            self.driver.check(resource)

    def test_check_fail_invalid_ip1(self):
        resource = make_resource(address='10.0.1.1')
        self.assertRaises(
            exceptions.ResourceCheckFailed, self.driver.check, resource)

    def test_check_fail_invalid_ip2(self):
        resource = make_resource(address='chubaca')
        self.assertRaises(
            exceptions.ResourceCheckFailed, self.driver.check, resource)

    def test_check_fail_not_connected(self):
        resource = make_resource()
        with self._check_check_instance(resource['address']):
            self.httpconn_cls.return_value = None
            self.assertRaises(
                exceptions.ResourceCheckFailed, self.driver.check, resource)

    def test_check_fail_socket_timeout(self):
        resource = make_resource()
        with self._check_check_instance(resource['address']):
            self.httpconn.getresponse.side_effect = socket.timeout()
            self.assertRaises(
                exceptions.ResourceCheckFailed, self.driver.check, resource)

    def test_check_fail_socket_error(self):
        resource = make_resource()
        with self._check_check_instance(resource['address']):
            self.httpconn.getresponse.side_effect = socket.error()
            self.assertRaises(
                exceptions.ResourceCheckFailed, self.driver.check, resource)

    def test_check_non_started(self):
        resource = make_resource(state=resources.STATE_ERROR)
        self.httpconn_cls.side_effect = AssertionError(
            "Shouldn't check resources in error state.")
        self.driver.check(resource)

    def test_init(self):
        resource = make_resource(state=resources.STATE_STOPPED, address=None,
                                 instance_id=None)
        with self._check_init():
            self.driver.init(resource)

    def test_init_instance_error_state(self):
        resource = make_resource(state=resources.STATE_STOPPED, address=None,
                                 instance_id=None)
        with self._check_init(instance_state='ERROR'):
            self.assertRaises(
                exceptions.DriverException, self.driver.init, resource)

    def test_init_initial_get_raises(self):
        resource = make_resource(state=resources.STATE_STOPPED, address=None,
                                 instance_id=None)
        with self._check_init():
            server = self.novaclient.servers.create.return_value
            self.novaclient.servers.get.side_effect = [RuntimeError(), server]
            self.driver.init(resource)

    def test_init_too_much_interfaces(self):
        resource = make_resource(state=resources.STATE_STOPPED, address=None,
                                 instance_id=None)
        with self._check_init(num_ifaces=2):
            self.assertRaises(
                exceptions.DriverException, self.driver.init, resource)

    def test_init_too_much_ips(self):
        resource = make_resource(state=resources.STATE_STOPPED, address=None,
                                 instance_id=None)
        with self._check_init(num_ips=2):
            self.assertRaises(
                exceptions.DriverException, self.driver.init, resource)

    def test_init_two_get_instance_calls(self):
        resource = make_resource(state=resources.STATE_STOPPED, address=None,
                                 instance_id=None)
        with self._check_init():
            server = self.novaclient.servers.create.return_value
            spawning_server = mock.MagicMock()
            spawning_server.status = 'BUILD'
            self.novaclient.servers.get.side_effect = [spawning_server, server]
            self.httpconn = mock.MagicMock()
            self.httpconn_cls.side_effect = [None, self.httpconn]
            self.driver.init(resource)

    def test_init_nova_timeout(self):
        resource = make_resource(state=resources.STATE_STOPPED, address=None,
                                 instance_id=None)
        with self._check_init(instance_state='BUILD'):
            self.time.side_effect = [1, 1 << 31]
            self.assertRaises(
                exceptions.DriverException, self.driver.init, resource)

    def test_makes_100_coverage(self):
        self.driver.wipe(None)
