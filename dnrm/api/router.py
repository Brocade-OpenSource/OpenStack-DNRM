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

from dnrm import api
from dnrm.api import collections
from dnrm.api import drivers
from dnrm.api import resources
from dnrm.api import versions


class APIRouter(api.APIRouter):
    def _setup_routes(self, mapper):
        self.resources['versions'] = versions.create_resource()
        mapper.connect("versions", "/",
                       controller=self.resources['versions'],
                       action='index',
                       conditions={'method': ['GET']})

        self.resources['collections'] = collections.create_resource()
        mapper.connect("collections", "/v1/",
                       controller=self.resources['collections'],
                       action='index',
                       conditions={'method': ['GET']})

        self.resources['resources'] = resources.create_resource()
        mapper.connect("resource", "/v1/resources/",
                       controller=self.resources['resources'],
                       action='index',
                       conditions={'method': ['GET']})

        mapper.connect("resource", "/v1/resources/",
                       controller=self.resources['resources'],
                       action='create',
                       conditions={'method': ['POST']})

        mapper.connect("resource", "/v1/resources/{resource_id}",
                       controller=self.resources['resources'],
                       action='show',
                       conditions={'method': ['GET']})

        mapper.connect("resource", "/v1/resources/{resource_id}",
                       controller=self.resources['resources'],
                       action='update',
                       conditions={'method': ['PUT']})

        mapper.connect("resource", "/v1/resources/{resource_id}",
                       controller=self.resources['resources'],
                       action='delete',
                       conditions={'method': ['DELETE']})

        self.resources['drivers'] = drivers.create_resource()
        mapper.connect("driver", "/v1/drivers/",
                       controller=self.resources['drivers'],
                       action='index',
                       conditions={'method': ['GET']})

        mapper.connect("driver", "/v1/drivers/{resource_type}",
                       controller=self.resources['drivers'],
                       action='show',
                       conditions={'method': ['GET']})
