#!/usr/bin/env python
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 Eugene Frolov <profisphantom@gmail.com>.
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

import logging as std_logging

from oslo.config import cfg

from dnrm.common import config
from dnrm.exceptions import wsgi as wsgi_exc
from dnrm.openstack.common import log as logging
from dnrm import wsgi


LOG = logging.getLogger(__name__)


class WsgiService(object):
    """WSGI based services.

    For each api you define, you must also define these flags:
    :<api>_listen: The address on which to listen
    :<api>_listen_port: The port on which to listen

    """
    def __new__(cls, app_name='dnrm'):

        # Setup logging early, supplying both the CLI options and the
        # configuration mapping from the config file
        # We only update the conf dict for the verbose and debug
        # flags. Everything else must be set up in the conf file...
        # Log the options used when starting if we're in debug mode...

        config.setup_logging(cfg.CONF)
        # Dump the initial option values
        cfg.CONF.log_opt_values(LOG, std_logging.DEBUG)
        return super(WsgiService, cls).__new__(cls, app_name)

    def __init__(self, app_name='dnrm'):
        self.app_name = app_name
        self.wsgi_app = None

    def start(self):
        app = config.load_paste_app(self.app_name)
        if not app:
            raise wsgi_exc.NoKnownApplications()
        self.wsgi_app = wsgi.Server(self.app_name)
        self.wsgi_app.start(app, cfg.CONF.bind_port, cfg.CONF.bind_host)
        # Dump all option values here after all options are parsed
        cfg.CONF.log_opt_values(LOG, std_logging.DEBUG)
        LOG.info(_("p2 service started, listening on %(host)s:%(port)s"),
                 {'host': cfg.CONF.bind_host,
                  'port': cfg.CONF.bind_port})
        return self

    def wait(self):
        self.wsgi_app.wait()
        return self
