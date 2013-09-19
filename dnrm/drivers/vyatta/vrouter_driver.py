# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack Foundation.
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
import httplib
import netaddr
import os
import socket
import time

from dnrm.drivers import base
from dnrm import exceptions
from dnrm import resources
from eventlet import greenthread
from oslo.config import cfg

from novaclient.v1_1 import client as novaclient

cfg.CONF.register_opts([
    cfg.IntOpt('api_port', default=5000,
               help=_('On which port DNRM API proxy for Vyatta vRouter '
                      'runs.')),
    cfg.StrOpt('api_public_key',
               help=_('Vyatta API proxy private key.')),
    cfg.StrOpt('api_private_key',
               help=_('Vyatta API proxy public key.')),
    cfg.StrOpt('tenant',
               help=_('UUID of tenant that holds Vyatta vRouter instances.')),
    cfg.StrOpt('tenant_admin_name', help=_('Name of tenant admin user.')),
    cfg.StrOpt('tenant_admin_password', help=_('Tenant admin password.')),
    cfg.StrOpt('keystone_url', help=_('Keystone URL.')),
    cfg.StrOpt('image_id',
               help=_('Nova image id for instances of Vyatta vRouter.')),
    cfg.StrOpt('flavor',
               help=_('Nova VM flavor for instances of Vyatta vRouter.')),
    cfg.StrOpt('management_network_id',
               help=_('UUID of Vyatta vRouter management network.')),
    cfg.StrOpt('management_network_cidr',
               help=_('CIDR of Vyatta vRouter management network.')),
    cfg.IntOpt('nova_poll_interval', default=5,
               help=_('Number of seconds between consecutive Nova queries '
                      'when waitong for server status change.')),
    cfg.IntOpt('nova_spawn_timeout', default=600,
               help=_('Number of seconds to wait for Nova to activate '
                      'instance before setting resource to error state.')),
    cfg.IntOpt('vrouter_poll_interval', default=5,
               help=_('Number of seconds between consecutive Vyatta vRouter '
                      'queries when waitong for server boot.')),
    cfg.IntOpt('vrouter_boot_timeout', default=600,
               help=_('Number of seconds to wait for Vyatta vRouter to boot '
                      'before setting resource to error state.')),
], "VROUTER")


class InvalidResourceAddress(exceptions.DriverException):
    message = _("Vyatta vRouter instance IP address %(address)s is not in "
                "management subnet.")


class InstanceSpawnError(exceptions.DriverException):
    message = _("Failed to launch vRouter instance.")


class InvalidInstanceConfiguration(exceptions.DriverException):
    message = _("Invalid configuration: %(cause)s.")


class InstanceBootTimeout(exceptions.DriverException):
    message = _("Timeout waiting for instance to boot.")


class VyattaVRouterDriver(base.DriverBase):
    resource_type = 'nova_vm'

    def __init__(self):
        self.management_net = netaddr.IPNetwork(
            cfg.CONF.VROUTER.management_network_cidr)
        self.admin_login = cfg.CONF.VROUTER.tenant_admin_name
        self.admin_password = cfg.CONF.VROUTER.tenant_admin_password
        self.keystone_url = cfg.CONF.VROUTER.keystone_url
        self.tenant = cfg.CONF.VROUTER.tenant
        self.flavor = cfg.CONF.VROUTER.flavor
        self.image_id = cfg.CONF.VROUTER.image_id
        self.net_id = cfg.CONF.VROUTER.management_network_id
        self.nova_interval = cfg.CONF.VROUTER.nova_poll_interval
        self.vrouter_interval = cfg.CONF.VROUTER.vrouter_poll_interval
        self.nova_timeout = cfg.CONF.VROUTER.nova_spawn_timeout
        self.vrouter_timeout = cfg.CONF.VROUTER.vrouter_boot_timeout
        self.api_port = cfg.CONF.VROUTER.api_port

    def init(self, resource):
        if resource.state != resources.STATE_STOPPED:
            return

        name = 'vrouter_{0}'.format(os.urandom(6).encode('hex'))
        client = self._nova_client()
        server = client.servers.create(name, self.image_id, self.flavor,
                                       nics=[{'net-id': self.net_id}])

        # Wait for Nova to start to boot VM instance
        def server_active():
            while True:
                try:
                    updated = client.servers.get(server.id)
                except Exception:
                    yield self.nova_interval
                    continue
                if updated.status not in ('ACTIVE', 'ERROR'):
                    yield self.nova_interval
                elif updated.status == 'ERROR':
                    raise InstanceSpawnError()
                else:
                    break
        self._wait(server_active, timeout=self.nova_timeout)

        # When VM is ready we can get list of attached interfaces and retreive
        # IP address
        interfaces = server.interface_list()
        if len(interfaces) != 1:
            # TODO(anfrolov): replace by meaningful exception
            raise InvalidInstanceConfiguration(
                cause=_("number of interfaces = %s") % len(interfaces))
        fixed_ips = interfaces[0].fixed_ips
        if len(fixed_ips) != 1:
            raise InvalidInstanceConfiguration(
                cause=_("number of fixed ips = %s") % len(fixed_ips))
        address = fixed_ips[0].ip_address
        resource.instance_id = server.id
        resource.address = address

        # Now wait for server to boot
        def server_boot():
            while not self._check_instance(address):
                yield self.vrouter_interval
        self._wait(server_boot, timeout=self.vrouter_timeout)

    def stop(self, resource):
        if resource.state != resources.STATE_STARTED:
            return
        client = self._nova_client()
        client.servers.delete(resource.instance_id)

    def wipe(self, resource):
        # TODO(anfrolov): Implement when wipe will be implemented in proxy
        pass

    def check(self, resource):
        if resource.state != resources.STATE_STARTED:
            return
        try:
            address = resource.address
            self._validate_address(address)
        except Exception as ex:
            raise exceptions.ResourceCheckFailed(error=str(ex))
        if not self._check_instance(address):
            raise exceptions.ResourceCheckFailed(error='failed to connect')

    def _nova_client(self):
        # TODO(anfrolov): cache keystone token
        return novaclient.Client(
            self.admin_login, self.admin_password, None, self.keystone_url,
            service_type='compute', tenant_id=self.tenant)

    def _wait(self, query_fn, timeout=0):
        # TODO(anfrolov): Implement when TaskQueue will be ready
        end = time.time() + timeout
        for interval in query_fn():
            greenthread.sleep(interval)
            if timeout > 0 and time.time() >= end:
                raise InstanceBootTimeout()

    def _check_instance(self, address):
        conn = httplib.HTTPConnection(address, self.api_port)
        if not conn:
            return False
        try:
            conn.request('GET', '/v2.0/router')
            response = conn.getresponse()
            if response.status == 401:
                return True
        except (socket.timeout, socket.error):
            return False
        finally:
            conn.close()

    def _validate_address(self, address):
        try:
            address = netaddr.IPAddress(address)
        except Exception as ex:
            raise InvalidResourceAddress(message=str(ex))
        if address not in self.management_net:
            raise InvalidResourceAddress(address=address)
