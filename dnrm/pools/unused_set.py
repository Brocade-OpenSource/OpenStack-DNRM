# vim: tabstop=4 shiftwidth=4 softtabstop=4

#    Copyright 2011 OpenStack Foundation
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

from dnrm import db


class UnusedSet(object):
    def __init__(self, resource_type, resource_factory):
        self.resource_type = resource_type
        self.resource_factory = resource_factory

    def get(self, status, count=None):
        resources = self.list(status, count)
        for resource in resources:
            res = db.resource_update(resource['id'], {'processing': True})
            resource.update(res)
        if len(resources) < (count or 0):
            try:
                for _i in xrange(count):
                    res = self.resource_factory.create(self.resource_type,
                                                       status)
                    res = db.resource_create(self.resource_type, res)
                    resources.append(res)
            except NotImplementedError:
                pass

    def list(self, status, count=None):
        filter_opts = {'filters': {'type': self.resource_type, 'pool': None,
                                   'allocated': False, 'processing': False,
                                   'status': status}}
        if count is not None:
            filter_opts['limit'] = count
        resources = db.resource_find(filter_opts)
        if not resources and count is None:
            return []
        return resources
