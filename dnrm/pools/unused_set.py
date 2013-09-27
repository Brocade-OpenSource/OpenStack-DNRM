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


class UnusedSet(object):
    def __init__(self, driver_name, driver_factory):
        self.driver_name = driver_name
        self.driver_factory = driver_factory

    def get(self, state, count=None):
        resources = self.list(state, count)
        for resource in resources:
            res = db.resource_update(resource['id'], {'processing': True})
            resource.update(res)
        if len(resources) < (count or 0):
            try:
                for _i in xrange(count):
                    driver = self.driver_factory.get(self.driver_name)
                    resource = driver.prepare_resource(state)
                    resource['processing'] = True
                    resource['driver'] = self.driver_name
                    resource = db.resource_create(driver.resource_type,
                                                  resource)
                    resources.append(resource)
            except NotImplementedError:
                pass
        return resources

    def list(self, state, count=None):
        filter_opts = {'filters': {'type': self.driver_name, 'pool': None,
                                   'allocated': False, 'processing': False,
                                   'deleted': False, 'status': state}}
        if count is not None:
            filter_opts['limit'] = count
        resources = db.resource_find(filter_opts)
        if not resources and count is None:
            return []
        return resources

    def count(self, state, processing=False):
        filter_opts = {'filters': {'type': self.driver_name, 'pool': None,
                                   'allocated': False, 'status': state,
                                   'processing': processing, 'deleted': False}}
        return db.resource_count(filter_opts)
