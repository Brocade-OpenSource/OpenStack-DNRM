# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack Foundation.
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

from eventlet import greenthread
from eventlet import queue
from oslo.config import cfg

from dnrm.db import api as db_api
from dnrm.openstack.common import log

CONF = cfg.CONF
LOG = log.getLogger(__name__)


class Worker(object):
    """Abstract base class for workers."""

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def run(self):
        """Method that doing the work."""
        pass

    @abc.abstractmethod
    def start(self):
        """Notifies worker that it should start working."""
        pass

    @abc.abstractmethod
    def stop(self):
        """Notifies worker that it should stop working."""
        pass


class QueuedTaskWorker(Worker):
    """
    Worker that takes tasks from task queue and executes them in loop.
    """

    def __init__(self, queue):
        self._queue = queue
        self._running = False
        self._timeout = CONF.task_queue_timeout

    def run(self):
        while self._running:
            # Drop reference to python object before blocking on pop
            task = None
            task = self._queue.pop(timeout=self._timeout)
            if task is None:
                continue
            try:
                resource = task.execute()
                resource.processing = False
                db_api.resource_update(resource.id, resource.to_dict())
            except Exception:
                LOG.exception(_('Exception executing task %s.') % repr(task))

    def start(self):
        if not self._running:
            self._running = True
            greenthread.spawn_n(self.run)

    def stop(self):
        self._running = False


class TaskQueue(object):
    """
    Manages task queue for workers.
    """

    def __init__(self):
        self._queue = queue.LightQueue()

    def push(self, task):
        """
        Adds new task to queue. Unblocks one worker waiting on pop call if
        there is any.
        """
        self._queue.put(task)

    def pop(self, block=True, timeout=None):
        """
        Removes task from queue. If optional arg block is true and timeout is
        None (the default), block if necessary until task is available. If
        timeout is a positive number, it blocks at most timeout seconds and
        returns None if no task was available within that time. Otherwise
        (block is false), return task if one is immediately available, else
        return None (timeout is ignored in that case).
        """
        try:
            return self._queue.get(block=block, timeout=timeout)
        except queue.Empty:
            return None
