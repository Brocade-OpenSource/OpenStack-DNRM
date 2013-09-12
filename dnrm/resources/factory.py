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
import glob
import os

from dnrm import exceptions
from dnrm.openstack.common import importutils
from dnrm.openstack.common import log
from dnrm.resources import base

LOG = log.getLogger(__name__)


class ResourceFactory(object):
    """
    Manages list of available resource types and allows to create resource
    by it's name.
    """

    def __init__(self):
        pattern = os.path.dirname(__file__) + '/*.py'
        base_module = __name__.rsplit('.', 1)[0] + '.'
        modules = [base_module + os.path.basename(f)[:-3]
                   for f in glob.glob(pattern)]
        self.resource_classes = {}
        for module_name in modules:
            try:
                module = importutils.import_module(module_name)
            except Exception:
                LOG.debug(
                    _('Failed to import resource module: %s') % module_name)
            for resource_class in module.__dict__.values():
                try:
                    if issubclass(resource_class, base.Resource):
                        resource_type = \
                            getattr(resource_class, 'type_name', None)
                        if resource_type is not None:
                            self.resource_classes[resource_type] = \
                                resource_class
                except TypeError:
                    pass

    def create(self, resource_type, state, resource_data=None):
        """Creates resource by it's type."""
        cls = self.resource_classes.get(resource_type)
        if cls is None:
            raise exceptions.InvalidResourceType(type_name=resource_type)
        if resource_data is not None:
            return cls.create(state, resource_data)
        else:
            return cls.create(state)

    def list_classes(self):
        """Returns list of all resource classes."""
        return self.resource_classes.values()

    def get_class(self, resource_type):
        """Returns resource class by it's name."""
        return self.resource_classes.get(resource_type)
