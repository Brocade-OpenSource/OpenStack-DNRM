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
import mock

from dnrm import db
from dnrm.openstack.common.fixture import mockpatch
from dnrm.tests import base


class ResourceTestCase(base.BaseTestCase):
    def setUp(self):
        super(ResourceTestCase, self).setUp()
        self.mock = self.useFixture(mockpatch.Patch('dnrm.db.api.IMPL',
                                                    new=mock.Mock())).mock

    def test_create(self):
        args = ['fake-resource', {}]
        db.resource_create(*args)
        self.mock.resource_create.assert_with_call(args)

    def test_delete(self):
        args = ['fake-resource-id']
        db.resource_delete(*args)
        self.mock.resource_delete.assert_with_call(args)

    def test_update(self):
        args = ['fake-resource-id', {}]
        db.resource_update(*args)
        self.mock.resource_update.assert_with_call(args)

    def test_get_by_id(self):
        args = ['fake-resource-id']
        db.resource_get_by_id(*args)
        self.mock.resource_get_by_id.assert_with_call(args)

    def test_count(self):
        args = [{}]
        db.resource_count(*args)
        self.mock.resource_count.assert_with_call(args)

    def test_find(self):
        args = [{}]
        db.resource_find(*args)
        self.mock.resource_find.assert_with_call(args)

    def test_compare_update(self):
        args = [0, {1: 2}, {3: 4}]
        db.resource_compare_update(*args)
        self.mock.resource_compare_update.assert_with_call(args)
