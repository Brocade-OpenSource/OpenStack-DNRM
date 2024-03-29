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
DNRM Supervisor resource and resource factory exceptions.
"""

from dnrm.exceptions import base


class InvalidResource(base.SupervisorException):
    message = _("Resource validation failed.")


class InvalidResourceType(base.SupervisorException):
    message = _('Invalid resource type name: %(type_name)s')


class ResourceAllocated(base.SupervisorException):
    message = _("Resource %(resource_id)s was been allocated.")


class ResourceProcessing(base.SupervisorException):
    message = _("Resource %(resource_id)s is processed.")
