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

import os

from oslo.config import cfg
from paste import deploy

from dnrm.openstack.common import log as logging
from dnrm.version import version_info as dnrm_version

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

core_opts = [
    cfg.StrOpt('bind_host', default='0.0.0.0',
               help=_("The host IP to bind to")),
    cfg.IntOpt('bind_port', default=8585,
               help=_("The port to bind to")),
    cfg.StrOpt('api_paste_config', default="api-paste.ini",
               help=_("The API paste config file to use")),
    cfg.StrOpt('auth_strategy', default='keystone',
               help=_("The type of authentication to use")),
    cfg.IntOpt('task_queue_timeout', default=5,
               help=_("Number of seconds for worker to wait on task queue.")),
    cfg.IntOpt('workers_count', default=5, help=_("Number of workers.")),
    cfg.StrOpt('balancer', default='dnrm.balancer.balancer.DNRMBalancer',
               help=_("The class of balancer")),
    cfg.IntOpt('sleep_time', default=30,
               help=_("The waiting time for a thread in seconds")),
]

CONF.register_opts(core_opts)

drivers_opts = [
    cfg.DictOpt('dnrm.drivers.vyatta.vrouter_driver.'
                'VyattaVRouterDriver', default={'low_watermark': 2,
                                                'high_watermark': 5}),
]
CONF.register_opts(drivers_opts, 'DRIVERS')


def parse(args):
    CONF(args=args, project='dnrm',
         version='%%prog %s' % dnrm_version.release_string())


def setup_logging(conf):
    """Sets up the logging options for a log with supplied name.

    :param conf: a cfg.ConfOpts object
    """
    product_name = "dnrm"
    logging.setup(product_name)
    LOG.info(_("Logging enabled!"))


def load_paste_app(app_name):
    """Builds and returns a WSGI app from a paste config file.

    :param app_name: Name of the application to load
    :raises RuntimeError when config file cannot be located or application
            cannot be loaded from config file
    """

    api_paste_config = CONF.find_file(CONF.api_paste_config)
    if not api_paste_config:
        msg = (_("Configuration file %(api_paste_config)s not found") %
               {"api_paste_config": CONF.api_paste_config})
        LOG.error(msg)
        raise RuntimeError(msg)
    config_path = os.path.abspath(api_paste_config)
    LOG.info(_("Config paste file: %s"), config_path)

    try:
        app = deploy.loadapp("config:%s" % config_path, name=app_name)
    except (LookupError, ImportError):
        msg = (_("Unable to load %(app_name)s from "
                 "configuration file %(config_path)s.") %
               {'app_name': app_name,
                'config_path': config_path})
        LOG.exception(msg)
        raise RuntimeError(msg)
    return app


def get_driver_config(driver_name):
    return CONF.DRIVERS.get(driver_name, {})


def get_drivers_names():
    return list(CONF.DRIVERS)
