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


class DriverBase(object):
    """
    Base class for DNRM supervisor resource drivers.
    """

    __metaclass__ = abc.ABCMeta

    resource_type = None

    @abc.abstractmethod
    def init(self, resource):
        """
        Initialize previously stopped resource. E.g. turn power on via IPMI or
        send REST request ton Nova to boot virtual machine.
        This function may issue long-runing operations.
        """
        pass

    @abc.abstractmethod
    def stop(self, resource):
        """
        Stops previously initialized resource. E.g. turn power off via IPMI or
        send REST request to Nova to terminate virtual machine.
        This function may issue long-runing operations.
        """
        pass

    @abc.abstractmethod
    def wipe(self, resource):
        """
        Return resource to it's initial state.
        This function may issue long-runing operations.
        """
        pass

    @abc.abstractmethod
    def check(self, resource):
        """
        Checks device availability status and throws exception if device is
        down. Do nothing if device is ok.
        This function may issue long-runing operations.
        """
        pass

    @abc.abstractmethod
    def validate_resource(self, resource):
        """
        Validates resource and throws exception on validation failure, or do
        nothing if resource is ok.
        """
        pass

    @abc.abstractmethod
    def schema(self):
        """
        Returns JSON schema for resources that are managed by this driver.
        """
        pass

    @abc.abstractmethod
    def prepare_resource(self, state):
        """Creates clean resource in requested state."""
        pass
