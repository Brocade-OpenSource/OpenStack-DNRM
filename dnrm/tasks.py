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
"""
Module contains task classes used by balancer.
"""
import abc

from dnrm.openstack.common import excutils
from dnrm.openstack.common import log
from dnrm.resources import base

LOG = log.getLogger(__name__)


class Task(object):
    """Base class for task objects."""

    __metaclass__ = abc.ABCMeta

    def __init__(self, resource):
        self._resource = resource

    @abc.abstractmethod
    def execute(self, driver_factory):
        """Called by task queue workers when they start to work on task."""
        pass

    def get_resource_id(self):
        """Returns resource id that task is working on."""
        return self._resource['id']


class StartTask(Task):
    """Task that puts resource to started state."""

    in_states = (base.STATE_STOPPED,)
    process_state = base.STATE_STARTING
    success_state = base.STATE_STARTED
    fail_state = base.STATE_ERROR

    def execute(self, driver_factory):
        resource = self._resource
        driver = driver_factory.get(resource['type'])
        driver.init(resource)
        return resource


class StopTask(Task):
    """Task that puts resource to stopped state."""

    in_states = (base.STATE_STARTED,)
    process_state = base.STATE_STOPPING
    success_state = base.STATE_STOPPED
    fail_state = base.STATE_ERROR

    def execute(self, driver_factory):
        resource = self._resource
        driver = driver_factory.get(resource['type'])
        driver.stop(resource)
        return resource


class WipeTask(Task):
    """Task that wipes task state."""

    in_states = (base.STATE_STARTED,)
    process_state = base.STATE_WIPING
    success_state = base.STATE_STARTED
    fail_state = base.STATE_ERROR

    def execute(self, driver_factory):
        resource = self._resource
        driver = driver_factory.get(resource['type'])
        driver.wipe(resource)
        return resource


class DeleteTask(Task):
    """Task that marks resource as deleted."""

    in_states = (base.STATE_ERROR, base.STATE_STOPPED)
    process_state = base.STATE_DELETING
    success_state = base.STATE_DELETED
    fail_state = base.STATE_ERROR

    def __init__(self, resource, force=False):
        super(DeleteTask, self).__init__(resource)
        self._force = force

    def execute(self, driver_factory):
        resource = self._resource
        driver = driver_factory.get(resource['type'])
        try:
            driver.stop(resource)
        except Exception:
            with excutils.save_and_reraise_exception() as exc_reraiser:
                LOG.exception(_('Failed to delete resource'))
                exc_reraiser.reraise = not self._force
        return resource
