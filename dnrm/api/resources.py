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

import webob

from dnrm import wsgi

from dnrm.openstack.common import exception
from dnrm.openstack.common import log as logging
from dnrm.resources import manager
from webob import exc

LOG = logging.getLogger(__name__)


class ResourceController(wsgi.Controller):
    def __init__(self):
        self.resource_manager = manager.ResourceManager()
        super(ResourceController, self).__init__()

    def index(self, request):
        """Return a summary list of resources."""
        context = request.environ.get('dnrm.context', None)
        search_opts = {}
        search_opts.update(request.GET)
        return {'resources': self.resource_manager.list(context, search_opts)}

    def create(self, request, body):
        """Create a new resource."""
        context = request.environ.get('dnrm.context', None)
        LOG.audit(_("Creating new resource"))
        if not self.is_valid_body(body, 'resource'):
            raise exc.HTTPBadRequest()
        resource = body['resource']
        resource_type = resource.get('resource_type', None)
        self.resource_manager.add(context, resource_type, resource)

    def show(self, request, resource_id):
        """Get a resource."""
        context = request.environ.get('dnrm.context', None)
        try:
            resource = self.resource_manager.get(context, resource_id)
        except exception.NotFound:
            raise exc.HTTPNotFound()
        return {'resource': resource}

    def update(self, request, resource_id, body):
        """Update a resource."""
        context = request.environ.get('dnrm.context', None)
        LOG.audit(_("Updating new resource"))
        if not body:
            raise exc.HTTPBadRequest()
        if 'resource' not in body:
            raise exc.HTTPBadRequest()

        update_dict = body['resource']
        if 'status' in update_dict:
            del update_dict['status']
        if 'driver_name' in update_dict:
            del update_dict['driver_name']

        try:
            resource = self.resource_manager.get(context, resource_id)
        except exception.NotFound:
            raise exc.HTTPNotFound()

        allocate = update_dict.get('allocated', None)
        if allocate is not None:
            if allocate is True:
                resource = self.resource_manager.allocate(context,
                                                          resource['id'])
            else:
                resource = self.resource_manager.deallocate(context,
                                                            resource['id'])

        return {'resource': resource}

    def delete(self, request, resource_id):
        """Delete a resource."""
        context = request.environ.get('dnrm.context', None)
        LOG.audit(_("Delete resource with id: %s"), resource_id,
                  context=context)

        try:
            resource = self.resource_manager.get(context, resource_id)
            self.resource_manager.delete(context, resource['id'])
        except exception.NotFound:
            raise exc.HTTPNotFound()
        return webob.Response(status_int=204)


def create_resource():
    return wsgi.Resource(ResourceController())
