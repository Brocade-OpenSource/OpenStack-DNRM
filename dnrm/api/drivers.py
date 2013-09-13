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


from dnrm import wsgi

from dnrm.common import config
from dnrm.openstack.common import exception
from dnrm.openstack.common import log as logging
from dnrm.resources import manager
from webob import exc

LOG = logging.getLogger(__name__)


class DriverController(wsgi.Controller):
    def __init__(self):
        self.resource_manager = manager.ResourceManager()
        super(DriverController, self).__init__()

    def index(self, request):
        """Return a summary list of drivers."""
        return {'drivers': config.get_drivers_names()}

    def show(self, request, resource_type=None):
        """Get a driver."""
        context = request.environ.get('dnrm.context', None)
        try:
            driver = self.resource_manager.schema(context, resource_type)
        except exception.NotFound:
            raise exc.HTTPNotFound()
        return {'driver': driver}


def create_resource():
    return wsgi.Resource(DriverController())
