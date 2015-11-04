# Monocyte - Search and Destroy unwanted AWS Resources relentlessly.
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

import boto.exception
import boto.dynamodb2.table
import boto.regioninfo

from unittest import TestCase
from mock import patch, Mock
from monocyte.handler import dynamodb

TABLE_NAME = "mock_table"


class DynamoDbTableHandlerTest(TestCase):
    def setUp(self):
        self.dynamodb_mock = patch("monocyte.handler.dynamodb.dynamodb2").start()
        self.positive_fake_region = Mock(boto.regioninfo.RegionInfo)
        self.positive_fake_region.name = "allowed_region"
        self.negative_fake_region = Mock(boto.regioninfo.RegionInfo)
        self.negative_fake_region.name = "forbidden_region"

        self.dynamodb_mock.regions.return_value = [self.positive_fake_region, self.negative_fake_region]
        self.logger_mock = patch("monocyte.handler.logging").start()
        self.dynamodb_handler = dynamodb.Table(
            lambda region_name: region_name == self.positive_fake_region.name)

        self.instance_mock = self._given_instance_mock()
        connection = self.dynamodb_mock.connect_to_region.return_value
        connection.list_tables.return_value = {"TableNames": ["mock_table"]}
        connection.describe_table.return_value = self.instance_mock

    def tearDown(self):
        patch.stopall()

    def test_fetch_unwanted_resources_filtered_by_region(self):
        only_resource = list(self.dynamodb_handler.fetch_unwanted_resources())[0]
        self.assertEquals(only_resource.wrapped, self.instance_mock["Table"])

    def test_fetch_unwanted_resources_filtered_by_ignored_resources(self):
        self.dynamodb_handler.ignored_resources = [TABLE_NAME]
        empty_list = list(self.dynamodb_handler.fetch_unwanted_resources())
        self.assertEqual(empty_list, [])

    def test_to_string(self):
        only_resource = list(self.dynamodb_handler.fetch_unwanted_resources())[0]
        resource_string = self.dynamodb_handler.to_string(only_resource)

        self.assertTrue("mock_table" in resource_string)

    def _given_instance_mock(self):
        instance_mock = {"Table": {"TableName": TABLE_NAME, "CreationDateTime": 1, "TableStatus": "mocked"}}
        return instance_mock
