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
import abc

from dnrm import db
from dnrm.resources import base
from dnrm import tasks


class Balancer(object):
    __meta__ = abc.ABCMeta

    def __init__(self, pool, unused_set, low_watermark, high_watermark):
        self._pool = pool
        self._unused_set = unused_set
        self.low_watermark = low_watermark
        self.high_watermark = high_watermark

    def get_resources(self, state, count=None):
        return self._unused_set.get(state, count)

    def list_resources(self, state, count=None):
        return self._unused_set.list(state, count)

    def push_resources(self, resources):
        for resource in resources:
            self._pool.push(resource)

    def pop_resources(self, count=None):
        return self._pool.pop(count)

    def start(self, resource):
        if resource['state'] == base.STATE_STOPPED:
            resource.update(db.resource_update(
                resource['id'], {'state': base.STATE_STARTED}))

    def stop(self, resource):
        if resource['state'] == base.STATE_STARTED:
            resource.update(db.resource_update(
                resource['id'], {'state': base.STATE_STOPPED}))

    @abc.abstractmethod
    def balance(self):
        pass

    def __str__(self):
        return self._pool.name


class TaskBasedBalancer(Balancer):
    def __init__(self, pool, unused_set, low_watermark, high_watermark,
                 queue):
        super(TaskBasedBalancer, self).__init__(pool, unused_set,
                                                low_watermark, high_watermark)
        self._queue = queue

    def start(self, resource):
        super(TaskBasedBalancer, self).start(resource)
        task = tasks.StartTask(resource)
        self._queue.push(task)

    def stop(self, resource):
        super(TaskBasedBalancer, self).stop(resource)
        task = tasks.StopTask(resource)
        self._queue.push(task)


class SimpleBalancer(Balancer):
    def eliminate_deficit(self, deficit):
        resources = self.list_resources(base.STATE_STARTED, deficit)
        self.push_resources(resources)
        deficit -= len(resources)
        if deficit > 0:
            resources = self.get_resources(base.STATE_STOPPED, deficit)
            for resource in resources:
                self.start(resource)

    def eliminate_overflow(self, overflow):
        resources = self.pop_resources(overflow)
        for resource in resources:
            self.stop(resource)

    def stop_unused(self):
        started = self.list_resources(base.STATE_STARTED)
        for resource in started:
            self.stop(resource)

    def balance(self):
        # Eliminate deficit.
        deficit = (self.low_watermark - self._pool.count() -
                   self._unused_set.count(base.STATE_STARTED, True))
        if deficit > 0:
            self.eliminate_deficit(deficit)

        # Eliminate overflow
        overflow = self._pool.count() - self.high_watermark
        if overflow > 0:
            self.eliminate_overflow(overflow)

        # Stop unused started resources
        self.stop_unused()


class DNRMBalancer(SimpleBalancer, TaskBasedBalancer):
    pass
