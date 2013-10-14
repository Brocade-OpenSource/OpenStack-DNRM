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
import eventlet
from oslo.config import cfg

from dnrm import db
from dnrm.openstack.common import log
from dnrm.resources import base

CONF = cfg.CONF
LOG = log.getLogger(__name__)


class Cleaner(object):
    def __init__(self):
        self._running = False

    def run(self):
        while self._running:
            resources = db.resource_find(
                {'filters': {'processing': False,
                             'status': base.STATE_DELETED}}
            )
            for resource in resources:
                LOG.debug(_('Delete resource %s'), resource['id'])
                db.resource_delete(resource['id'])
            eventlet.sleep(CONF.sleep_time)

    def start(self):
        if self._running:
            return
        self._running = True
        eventlet.spawn_n(self.run)

    def stop(self):
        self._running = False
