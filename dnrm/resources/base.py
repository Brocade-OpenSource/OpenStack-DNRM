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
STATE_STOPPED = 'STOPPED'
STATE_STARTED = 'STARTED'
STATE_ERROR = 'ERROR'
STATE_DELETED = 'DELETED'
STATE_STARTING = 'STARTING'
STATE_STOPPING = 'STOPPING'
STATE_DELETING = 'DELETING'
STATE_WIPING = 'WIPING'
ACTIVE_STATES = (STATE_STARTED, STATE_STARTING, STATE_WIPING)
