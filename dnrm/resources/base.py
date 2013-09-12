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
STATE_STOPPED = 'STOPPED'
STATE_STARTED = 'STARTED'
STATE_ERROR = 'ERROR'


class Resource(object):
    """
    Base class for DNRM supervisor resources.
    """

    def __init__(self, resource_data=None):
        self.__dict__['_data'] = {'state': STATE_STOPPED}
        if resource_data is not None:
            self._data.update(resource_data)
            self.__class__.validate(self._data)

    def __getattr__(self, name):
        if name in self._data:
            return self._data[name]
        else:
            raise AttributeError("%r object has no attribute %r" %
                                 (self.__class__, name))

    def __setattr__(self, name, value):
        self._data[name] = value

    @classmethod
    def create(cls, state, resource_data=None):
        """
        Resources that can be created automatically (e.g. virtual machines)
        should overload this method.
        """
        raise NotImplementedError()

    @classmethod
    def validate(cls, resource_data):
        """
        Validates resource and throws exception on validation failure, or do
        nothing if resource is ok.
        """
        raise NotImplementedError()

    @classmethod
    def schema(cls):
        """
        Validates resource and throws exception on validation failure, or do
        nothing if resource is ok.
        """
        raise NotImplementedError()
