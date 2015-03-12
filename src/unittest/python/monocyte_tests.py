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

from unittest import TestCase
from boto.regioninfo import RegionInfo
from mock import Mock, patch
from monocyte import Monocyte, fetch_all_handler_classes
from monocyte.handler import Resource, Handler

REGION_NOT_ALLOWED = "test handler"


class MonocyteTest(TestCase):

    def setUp(self):
        self.logger_mock = patch("monocyte.logging").start()
        self.logger_mock.INFO = 20
        self.monocyte = Monocyte()
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
        handler.fetch_unwanted_resources.return_value = [Resource("foo", "test_region")]
        handler.to_string.return_value = "test handler"
        self.monocyte.handle_service(handler)

        self.logger_mock.getLogger.return_value.info.assert_called_with(REGION_NOT_ALLOWED)

    def test_fetch_all_handler_classes(self):
        classes = fetch_all_handler_classes()
        self.assertTrue(len(classes) > 0)
        for cls in classes:
            self.assertTrue(cls.startswith("monocyte"))
            self.assertTrue("andler" in cls)

    @patch("monocyte.fetch_all_handler_classes", create=True)
    def test_search_and_destroy_unwanted_resources_dry_run(self, fetch_mock):
        fetch_mock.return_value = {"monocyte.handler.dummy": DummyHandler}
        self.monocyte.search_and_destroy_unwanted_resources(["dummy"])

    @patch("monocyte.fetch_all_handler_classes", create=True)
    def test_search_and_destroy_unwanted_resources(self, fetch_mock):
        fetch_mock.return_value = {"monocyte.handler.dummy": DummyHandler}
        self.monocyte.search_and_destroy_unwanted_resources(["dummy"], dry_run=False)


class DummyHandler(Handler):
    def fetch_unwanted_resources(self):
        return [Resource(Mock(), "us")]

    def fetch_regions(self):
        mock = Mock(RegionInfo)
        mock.name = "us"
        return [mock]

    def to_string(self, resource):
        pass

    def delete(self, resource):
        if self.dry_run:
            return
        raise Exception("boo")
