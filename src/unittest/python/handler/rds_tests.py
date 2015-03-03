# Monocyte - An AWS Resource Destroyer
# Copyright 2015 Immobilien Scout GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import boto.rds2
import boto.regioninfo
from unittest import TestCase
from mock import patch, Mock
from monocyte.handler import rds2


class RDSHandlerTest(TestCase):
    def setUp(self):
        self.boto_mock = patch("monocyte.handler.rds2.boto").start()
        self.instance_mock = self._given_instance_mock()

        self.positive_fake_region = Mock(boto.regioninfo.RegionInfo)
        self.positive_fake_region.name = "allowed_region"
        self.negative_fake_region = Mock(boto.regioninfo.RegionInfo)
        self.negative_fake_region.name = "forbidden_region"
        self.boto_mock.rds2.regions.return_value = [self.positive_fake_region, self.negative_fake_region]
        self.rds_instance = rds2.Instance(lambda region_name: True)

    def tearDown(self):
        patch.stopall()

    def test_fetch_unwanted_resources_filtered(self):
        self.boto_mock.rds2.connect_to_region.return_value.describe_db_instances.return_value = \
            self._given_db_instances_response()

        only_resource = list(self.rds_instance.fetch_unwanted_resources())[0]
        self.assertEquals(only_resource.wrapped, self.instance_mock)

    def _given_db_instances_response(self):
        return {
            'DescribeDBInstancesResponse': {
                'DescribeDBInstancesResult': {
                    'DBInstances': [self.instance_mock]
                }
            }
        }

    def _given_instance_mock(self):
        instance_mock = {
            "DBInstanceIdentifier": "myInstanceIdentifier",
            "DBInstanceStatus": "myStatus"
        }
        return instance_mock
