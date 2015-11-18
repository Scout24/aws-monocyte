# Monocyte - Search and Destroy unwanted AWS Resources relentlessly.
# Copyright 2015 Immobilien Scout GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
import datetime
from unittest import TestCase
from boto.regioninfo import RegionInfo
from mock import Mock, patch

from monocyte import Monocyte
from monocyte.handler import Resource, Handler
from monocyte.cli import apply_default_config


REGION_NOT_ALLOWED = "test handler"


class MonocyteTest(TestCase):

    def setUp(self):
        self.logger_mock = patch("monocyte.logging").start()
        self.logger_mock.INFO = 20
        self.config = {
            "handler_names": ["dummy"]
        }
        apply_default_config(self.config)
        self.monocyte = Monocyte(**self.config)

        self.allowed_region = "EU"
        self.not_allowed_region = "US"
        self.ignored_region = "us-gov-west-1"

    def test_is_region_allowed(self):
        self.assertTrue(self.monocyte.is_region_allowed(self.allowed_region))
        self.assertFalse(self.monocyte.is_region_allowed(self.not_allowed_region))

    def test_is_region_ignored(self):
        self.assertTrue(self.monocyte.is_region_ignored(self.ignored_region))
        self.assertFalse(self.monocyte.is_region_ignored(self.allowed_region))

    def test_is_region_handled(self):
        self.assertFalse(self.monocyte.is_region_handled(self.allowed_region))
        self.assertFalse(self.monocyte.is_region_handled(self.ignored_region))

    def test_handle_service(self):
        handler = Mock()
        handler.fetch_unwanted_resources.return_value = [Resource(
            "foo", "test_type", "test_id", datetime.datetime.now(), "test_region")]
        handler.to_string.return_value = "test handler"
        self.monocyte.handle_service(handler)

        self.logger_mock.getLogger.return_value.warn.assert_called_with(REGION_NOT_ALLOWED)

    @patch("monocyte.Monocyte.get_all_handler_classes")
    def test_search_and_destroy_unwanted_resources_dry_run(self, fetch_mock):
        fetch_mock.return_value = {"monocyte.handler.dummy": DummyHandler}
        self.monocyte.search_and_destroy_unwanted_resources()
        dummy_handler = DummyHandler(self.monocyte.is_region_handled)
        expected_unwanted_resources = dummy_handler.fetch_unwanted_resources()
        expected_resource_ids = set([resource.resource_id for resource in expected_unwanted_resources])
        result_resource_ids = set([resource.resource_id for resource in self.monocyte.unwanted_resources])
        self.assertEqual(sorted(expected_resource_ids), sorted(result_resource_ids.intersection(expected_resource_ids)))

    @patch("monocyte.Monocyte.get_all_handler_classes")
    def test_search_and_destroy_unwanted_resources(self, fetch_mock):
        fetch_mock.return_value = {"monocyte.handler.dummy": DummyHandler}
        self.monocyte.dry_run = False
        self.monocyte.search_and_destroy_unwanted_resources()
        dummy_handler = DummyHandler(self.monocyte.is_region_handled)
        expected_unwanted_resources = dummy_handler.fetch_unwanted_resources()
        expected_resource_ids = set([resource.resource_id for resource in expected_unwanted_resources])
        result_resource_ids = set([resource.resource_id for resource in self.monocyte.unwanted_resources])
        self.assertEqual(sorted(expected_resource_ids), sorted(result_resource_ids.intersection(expected_resource_ids)))


class DummyHandler(Handler):
    def fetch_unwanted_resources(self):
        return [Resource(Mock(), "ec2 instance", "123456789", datetime.datetime.now(), "us"),
                Resource(Mock(), "ec2 volume", "33123456789", datetime.datetime.now(), "us")]

    def fetch_regions(self):
        mock = Mock(RegionInfo)
        mock.name = "us"
        return [mock]

    def to_string(self, resource):
        pass

    def delete(self, resource):
        if self.dry_run:
            return
        return
