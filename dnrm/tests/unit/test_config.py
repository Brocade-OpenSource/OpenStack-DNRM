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
        vyatta = ('dnrm.drivers.vyatta.vrouter_driver.'
                  'VyattaVRouterDriver', {'low_watermark': 10,
                                          'high_watermark': 20})
        fake = ('dnrm.drivers.fake.FakeDriver', {'low_watermark': 10,
                                                 'high_watermark': 20})
        self.opts = dict([vyatta, fake])
        CONF.set_override(vyatta[0], vyatta[1], 'DRIVERS')
        CONF.register_opt(cfg.DictOpt(fake[0], default=fake[1]), 'DRIVERS')

    def test_drivers_names(self):
        names = config.get_drivers_names()
        self.assertListEqual(self.opts.keys(), names)

    def test_resource_config(self):
        for k, v in self.opts.items():
            conf = config.get_driver_config(k)
            self.assertDictEqual(v, conf)
