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
from dnrm import db


class Pool(object):
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name

    def push(self, resource_id):
        db.resource_update(resource_id, {'pool': self.name,
                                         'processing': False})

    def pop(self, count=1, processing=True):
        search_opts = {'filters': {'pool': self.name, 'allocated': False}}
        if count is not None:
            search_opts['limit'] = count
        resources = db.resource_find(search_opts)
        for resource in resources:
            resource.update(db.resource_update(resource['id'],
                                               {'pool': None,
                                                'processing': processing}))
        return resources

    def list(self):
        resources = db.resource_find({'filters': {'pool': self.name,
                                                  'allocated': False}})
        return resources

    def count(self):
        count = db.resource_count({'filters': {'pool': self.name,
                                               'allocated': False}})
        return count
