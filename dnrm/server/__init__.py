#!/usr/bin/env python
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

import sys

import eventlet
from oslo.config import cfg

from dnrm.common import config
from dnrm.service import WsgiService

# from dnrm.openstack.common import gettextutils
# gettextutils.install('dnrm', lazy=True)


def main():
    eventlet.monkey_patch()

    # the configuration will be read into the cfg.CONF global data structure
    config.parse(sys.argv[1:])

    if not cfg.CONF.config_file:
        sys.exit(_("ERROR: Unable to find configuration file via the default"
                   " search paths (~/.dnrm/, ~/, /etc/dnrm/, /etc/) and"
                   " the '--config-file' option!"))
    try:
        p2api = WsgiService()
        p2api.start().wait()
    except RuntimeError as e:
        sys.exit(_("ERROR: %s") % e)


if __name__ == "__main__":
    main()
