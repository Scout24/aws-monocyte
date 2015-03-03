# Monocyte - An AWS Resource Destroyer
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
from mock import Mock, patch
from monocyte import Monocyte
from monocyte.handler import Resource


class MonocyteTest(TestCase):

    def setUp(self):
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

    @patch("monocyte.print", create=True)
    def test_handle_service(self, print_mock):
        handler = Mock()
        handler.fetch_unwanted_resources.return_value = [Resource("foo", "test_region")]
        handler.to_string.return_value = "test handler"
        self.monocyte.handle_service(handler)

        print_mock.assert_called_with("\ntest handler\n\tWARNING: region 'test_region' not allowed!")
