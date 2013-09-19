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
import netaddr

from dnrm import exceptions
from dnrm.resources import base


class VirtualResource(base.Resource):
    """
    Resource represented by Nova VM instance and controlled through REST
    interface.
    """

    type_name = 'nova_vm'

    @classmethod
    def create(cls, state, resource_data=None):
        if state == base.STATE_STOPPED:
            return cls(resource_data)
        else:
            super(VirtualResource, cls).create(state, resource_data)

    @classmethod
    def validate(cls, resource_data):
        """
        Validates resource and throws exception on validation failure, or do
        nothing if resource is ok.
        """
        # Check address
        try:
            netaddr.IPAddress(resource_data['address'])
        except Exception as ex:
            raise exceptions.InvalidResource(message=str(ex))

        # Check instance_id
        if 'instance_id' not in resource_data:
            raise exceptions.InvalidResource(
                _('Vyatta vRouter instance UUID (instance_id) missing.'))

    @classmethod
    def schema(cls):
        """
        Returns JSON schema for resources that are managed by this driver.
        """
        return {
            'title': 'Vyatta vRouter resource object JSON schema.',
            'type': 'object',
            'properties': {
                'address': {'type': 'ip-address'},
                'instance_id': {
                    'type': 'string',
                    'minLength': 36,
                    'maxLength': 36
                },
            }
        }
