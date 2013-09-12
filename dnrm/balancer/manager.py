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

import eventlet
from oslo.config import cfg

from dnrm.openstack.common import importutils
from dnrm.openstack.common import log as logging

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class BalancersManager(object):
    __meta__ = abc.ABCMeta

    def __init__(self):
        self.balancers = {}

    def get_pool_key(self, pool):
        return pool.name

    @abc.abstractmethod
    def create_balancer(self, pool, unused_set,
                        low_watermark, high_watermark):
        pass

    def balancer_already_added(self, pool_key):
        return pool_key in self.balancers

    def add_balancer(self, pool, unused_set, low_watermark, high_watermark):
        pool_key = self.get_pool_key(pool)
        if self.balancer_already_added(pool_key):
            raise ValueError(_('Balancer for %s already added') % pool_key)
        balancer = self.create_balancer(pool, unused_set,
                                        low_watermark, high_watermark)
        self.balancers[pool_key] = balancer
        return balancer

    @abc.abstractmethod
    def balance_pools(self):
        pass


class SerialBalancersManager(BalancersManager):
    def balance_pools(self):
        for balancer in self.balancers.values():
            try:
                balancer.balance()
            except Exception as e:
                msg = _('Balancer {0} error: {1}').format(str(balancer),
                                                          str(e))
                LOG.error(msg)


class DNRMBalancersManager(SerialBalancersManager):
    def __init__(self, queue):
        super(DNRMBalancersManager, self).__init__()
        self.queue = queue
        self.threads = []
        self.is_runned = False
        self.BALANCER_CLASS = importutils.import_class(CONF.balancer)
        self.SLEEP = CONF.sleep_time

    def create_balancer(self, pool, unused_set,
                        low_watermark, high_watermark):
        return self.BALANCER_CLASS(pool, unused_set, low_watermark,
                                   high_watermark, self.queue)

    def balance_pools(self):
        while True:
            super(DNRMBalancersManager, self).balance_pools()
            eventlet.sleep(self.SLEEP)

    def join(self):
        for thread in self.threads:
            thread.wait()

    def run(self):
        if self.is_runned:
            return
        self.threads.append(eventlet.spawn(self.balance_pools))
        self.is_runned = True

    def kill(self):
        for thread in self.threads:
            eventlet.kill(thread)
        self.is_runned = False
