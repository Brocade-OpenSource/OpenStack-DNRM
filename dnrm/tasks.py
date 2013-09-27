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

from dnrm.resources import base


class Task(object):
    """Base class for task objects."""

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def execute(self, driver_factory):
        """Called by task queue workers when they start to work on task."""
        pass


class StartTask(Task):
    """Task that puts resource to started state."""

    def __init__(self, resource):
        self._resource = resource

    def execute(self, driver_factory):
        resource = self._resource
        driver = driver_factory.get(resource['driver'])
        driver.init(resource)
        resource['status'] = base.STATE_STARTED
        return resource


class StopTask(Task):
    """Task that puts resource to stopped state."""

    def __init__(self, resource):
        self._resource = resource

    def execute(self, driver_factory):
        resource = self._resource
        driver = driver_factory.get(resource['driver'])
        driver.stop(resource)
        resource['status'] = base.STATE_STOPPED
        if 'address' in resource:
            del resource['address']
        if 'instance_id' in resource:
            del resource['instance_id']
        return resource


class WipeTask(Task):
    """Task that wipes task state."""

    def __init__(self, resource):
        self._resource = resource

    def execute(self, driver_factory):
        resource = self._resource
        driver = driver_factory.get(resource['driver'])
        driver.wipe(resource)
        return resource


class DeleteTask(Task):
    """Task that marks resource as deleted."""

    def __init__(self, resource):
        self._resource = resource

    def execute(self, driver_factory):
        resource = self._resource
        driver = driver_factory.get(resource['driver'])
        driver.stop(resource)
        resource['deleted'] = True
        return resource
