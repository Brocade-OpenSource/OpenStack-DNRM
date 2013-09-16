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
from oslo.config import cfg

from dnrm.balancer import manager as balancer
from dnrm.common import config
from dnrm import db
from dnrm.drivers import factory as driver_factory
from dnrm import exceptions
from dnrm.pools import pool
from dnrm.pools import unused_set
from dnrm.resources import base as resources
from dnrm.resources import cleaner
from dnrm.resources import factory as resource_factory
from dnrm import task_queue
from dnrm import tasks

CONF = cfg.CONF


class ResourceManager(object):
    def __init__(self):
        self.task_queue = task_queue.TaskQueue()
        self.task_workers = []
        for _i in xrange(CONF.workers_count):
            t = task_queue.QueuedTaskWorker(self.task_queue)
            self.task_workers.append(t)
            t.start()
        self.driver_factory = driver_factory.DriverFactory()

        self.balancer_manager = balancer.DNRMBalancersManager(self.task_queue)
        self.resource_factory = resource_factory.ResourceFactory()
        self.pools = {}
        for driver_name in config.get_drivers_names():
            new_pool = pool.Pool(driver_name)
            new_unused_set = unused_set.UnusedSet(driver_name,
                                                  self.resource_factory,
                                                  self.driver_factory)
            conf = config.get_driver_config(driver_name)
            low_watermark = conf.get('low_watermark')
            high_watermark = conf.get('high_watermark')
            bal = self.balancer_manager.add_balancer(new_pool, new_unused_set,
                                                     low_watermark,
                                                     high_watermark)
            self.pools[driver_name] = {'pool': new_pool,
                                       'unused_set': new_unused_set,
                                       'balancer': bal}
        self.balancer_manager.run()
        self.cleaner = cleaner.Cleaner()
        self.cleaner.start()

    def close(self):
        self.balancer_manager.kill()
        self.balancer_manager.join()
        for t in self.task_workers:
            t.stop()
        for p in self.pools:
            p['pool'].pop(count=None, processing=False)
        self.cleaner.stop()

    def add(self, context, driver_name, resource_data):
        resource_type = self.driver_factory.get_resource_type(
            self.driver_name)
        resource = self.resource_factory.create(resource_type,
                                                resources.STATE_STOPPED,
                                                resource_data)
        resource = db.resource_create(self.driver_name, resource)
        return resource

    def delete(self, context, resource_id):
        resource = db.resource_get_by_id(resource_id)
        if resource['allocated']:
            raise exceptions.ResourceAllocated(resource_id=resource_id)

        resource = db.resource_update(resource_id, {'processing': True})
        task = tasks.DeleteTask(resource)
        self.task_queue.push(task)

    def allocate(self, context, resource_id):
        resource = db.resource_get_by_id(resource_id)
        if resource['allocated']:
            raise exceptions.ResourceAllocated(resource_id=resource_id)
        self.pools[resource['type']]['pool'].pop_resource(resource_id)
        resource = db.resource_update(resource_id, {'allocated': True,
                                                    'processing': False})
        return resource

    def deallocate(self, context, resource_id):
        resource = db.resource_update(resource_id, {'allocated': False,
                                                    'processing': True})
        task = tasks.WipeTask(resource)
        self.task_queue.push(task)

    def list(self, context, search_opts):
        return db.resource_find(search_opts)

    def get(self, context, resource_id):
        return db.resource_get_by_id(resource_id)

    def schema(self, context, resource_type):
        return self.resource_factory.get_class(resource_type).schema
