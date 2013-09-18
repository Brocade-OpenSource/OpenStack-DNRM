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
from oslo.config import cfg

from dnrm.common import config
from dnrm.tests import base

CONF = cfg.CONF


class ConfigTestCase(base.BaseTestCase):
    def setUp(self):
        super(ConfigTestCase, self).setUp()
        self.opts = {'dnrm.drivers.vyatta.vrouter_driver.'
                     'VyattaVRouterDriver': {'low_watermark': 10,
                                             'high_watermark': 20},
                     'dnrm.drivers.fake.FakeDriver': {'low_watermark': 10,
                                                      'high_watermark': 20}}
        opts = [cfg.DictOpt(k, default=v) for k, v in self.opts.items()]
        CONF.register_opts(opts, 'RESOURCES')

    def test_resource_types(self):
        types = config.get_resource_types()
        self.assertListEqual(self.opts.keys(), types)

    def test_resource_config(self):
        for k, v in self.opts.items():
            conf = config.get_resource_config(k)
            self.assertDictEqual(v, conf)
