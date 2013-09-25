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
from dnrm.common import config
from dnrm.drivers import base
from dnrm import exceptions
from dnrm.openstack.common import importutils
from dnrm.openstack.common import log

LOG = log.getLogger(__name__)


class DriverFactory(object):
    """
    Manages list of available resource types and allows to create resource
    by it's name.
    """

    def __init__(self):
        driver_class_names = config.get_drivers_names()
        self.driver_classes = {}
        self.driver_instances = {}
        for driver_class_name in driver_class_names:
            try:
                driver_class = importutils.import_class(driver_class_name)
                if issubclass(driver_class, base.DriverBase):
                    self.driver_classes[driver_class_name] = driver_class
            except Exception:
                LOG.exception(
                    _('Failed to import driver class: %s') % driver_class_name)

    def get(self, driver_name):
        """Creates resource by it's type."""
        if driver_name in self.driver_instances:
            return self.driver_instances[driver_name]
        elif driver_name in self.driver_classes:
            driver_class = self.driver_classes[driver_name]
            driver = driver_class()
            self.driver_instances[driver_name] = driver
            return driver
        else:
            raise exceptions.InvalidDriverName(driver_name=driver_name)

    def get_names(self, resource_type):
        drivers = []
        resource_type = resource_type.split('.') or ['com']
        for name, klass in self.driver_classes.items():
            dt = klass.resource_type.split('.')
            for i, p in enumerate(resource_type):
                try:
                    if dt[i] != p:
                        break
                except KeyError:
                    break
            else:
                drivers.append(name)
        return drivers
