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

from dnrm.openstack.common import log
from dnrm.resources import base
from dnrm import tasks

LOG = log.getLogger(__name__)


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
            LOG.debug(_('Push resource into pool: %(id)s/%(type)s') % resource)
            self._pool.push(resource['id'])

    def pop_resources(self, count=None):
        LOG.debug(_('Pop resources from pool: %(count)s') % {'count': 'all'
                                                             if count is None
                                                             else count})
        return self._pool.pop(count)

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
        super(TaskBasedBalancer, self).start(resource)
        LOG.debug(_('Start task for resource: %(id)s/%(type)s') % resource)
        task = tasks.StartTask(resource)
        self._queue.push(task)

    def stop(self, resource):
        super(TaskBasedBalancer, self).stop(resource)
        LOG.debug(_('Stop task for resource: %(id)s/%(type)s') % resource)
        task = tasks.StopTask(resource)
        self._queue.push(task)


class SimpleBalancer(Balancer):
    def eliminate_deficit(self, deficit):
        resources = self.get_resources(base.STATE_STARTED, deficit)
        LOG.debug(_('Eliminate deficit: %(real)d/%(deficit)d.') %
                  {'real': len(resources), 'deficit': deficit})
        self.push_resources(resources)
        deficit -= len(resources)
        if deficit > 0:
            resources = self.get_resources(base.STATE_STOPPED, deficit)
            for resource in resources:
                self.start(resource)

    def eliminate_overflow(self, overflow):
        resources = self.pop_resources(overflow)
        LOG.debug(_('Eliminate overflow: %(real)d/%(overflow)d.') %
                  {'real': len(resources), 'overflow': overflow})
        for resource in resources:
            self.stop(resource)

    def stop_unused(self):
        started = self.list_resources(base.STATE_STARTED)
        if started:
            LOG.debug(_('Stop unused: %(unused)d.') % {'unused': len(started)})
        for resource in started:
            self.stop(resource)

    def balance(self):
        LOG.debug(
            _('Run balancer for pool "%(name)s".\nLow watermark: %(low)d\n'
              'High watermark: %(high)d\nCurrent number: %(number)d\n') %
            {'name': self._pool.name, 'low': self.low_watermark,
             'high': self.high_watermark, 'number': self._pool.count()}
        )
        # Eliminate deficit.
        deficit = (self.low_watermark - self._pool.count() -
                   self._unused_set.count(base.ACTIVE_STATES, True))
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
