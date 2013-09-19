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

from dnrm.resources import base
from dnrm import tasks


class Balancer(object):
    __meta__ = abc.ABCMeta

    def __init__(self, pool, unused_set, low_watermark, high_watermark):
        self._pool = pool
        self._unused_set = unused_set
        self.low_watermark = low_watermark
        self.high_watermark = high_watermark

    def get_current_pool_size(self):
        return self._pool.get_count()

    def get_stopped_resources(self, count):
        return self._unused_set.get(base.STATE_STOPPED, count)

    def get_started_resources(self, count=None):
        return self._unused_set.get(base.STATE_STARTED, count)

    def push_resources_into_pool(self, resources):
        for resource in resources:
            self._pool.push(resource)

    def pop_resources_from_pool(self, n):
        return self._pool.pop(n)

    @abc.abstractmethod
    def start(self, resource):
        pass

    @abc.abstractmethod
    def stop(self, resource):
        pass

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
        task = tasks.StartTask(resource)
        self._queue.push(task)

    def stop(self, resource):
        task = tasks.StopTask(resource)
        self._queue.push(task)


class SimpleBalancer(Balancer):
    def eliminate_deficit(self, deficit):
        unused_resources = self.get_stopped_resources(deficit)
        for resource in unused_resources:
            self.start(resource)

    def eliminate_overflow(self, overflow):
        resources = self.pop_resources_from_pool(overflow)
        for resource in resources:
            self.stop(resource)

    def stop_unused_started_resources(self):
        started = self.get_started_resources()
        for resource in started:
            self.stop(resource)

    def balance(self):
        current_size = self.get_current_pool_size()

        # Push started resources into pool
        free_space = self.high_watermark - current_size
        if free_space > 0:
            started = self.get_started_resources(free_space)
            self.push_resources_into_pool(started)

        current_size = self.get_current_pool_size()

        # Eliminate deficit.
        deficit = self.low_watermark - current_size
        if deficit > 0:
            self.eliminate_deficit(deficit)

        current_size = self.get_current_pool_size()

        # Eliminate overflow
        overflow = current_size - self.high_watermark
        if overflow > 0:
            self.eliminate_overflow(overflow)

        # Stop unused started resources
        self.stop_unused_started_resources()


class DNRMBalancer(SimpleBalancer, TaskBasedBalancer):
    pass
