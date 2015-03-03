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

import boto.cloudformation
import boto.cloudformation.stack

from unittest import TestCase
from mock import patch, Mock

from monocyte.handler import cloudformation


class CloudFormationTest(TestCase):

    def setUp(self):
        self.boto_mock = patch("monocyte.handler.cloudformation.boto").start()
        self.positive_fake_region = Mock(boto.cloudformation.regions)
        self.positive_fake_region.name = "allowed_region"
        self.negative_fake_region = Mock(boto.cloudformation.regions)
        self.negative_fake_region.name = "forbbiden_region"
        self.boto_mock.cloudformation.regions.return_value = [self.positive_fake_region, self.negative_fake_region]

        self.cloudformation_handler_filter = cloudformation.Stack(lambda region_name: region_name == self.positive_fake_region.name)

        self.stack_mock = self._given_stack_mock()

    def tearDown(self):
        patch.stopall()

    def test_fetch_unwanted_resources_filtered(self):
        only_resource = list(self.cloudformation_handler_filter.fetch_unwanted_resources())[0]
        self.assertEquals(only_resource.wrapped, self.stack_mock)

    def test_to_string(self):
        only_resource = list(self.cloudformation_handler_filter.fetch_unwanted_resources())[0]
        resource_string = self.cloudformation_handler_filter.to_string(only_resource)

        self.assertTrue(self.stack_mock.stack_status in resource_string)
        self.assertTrue(self.stack_mock.creation_time in resource_string)
        self.assertTrue(self.stack_mock.region in resource_string)

    def test_delete(self):
        pass

    def _given_stack_mock(self):
        stack_mock = Mock(boto.cloudformation.stack.Stack, stack_name="test-stack")
        stack_mock.stack_id = "id-12345"
        stack_mock.stack_status = "CREATE_COMPLETE"
        stack_mock.creation_time = "01.01.2015"
        stack_mock.region = self.positive_fake_region.name

        self.boto_mock.cloudformation.connect_to_region.return_value.valid_states = ('CREATE_COMPLETE',
                                                                                     'DELETE_COMPLETE')
        self.boto_mock.cloudformation.connect_to_region.return_value.list_stacks.return_value = [stack_mock]
        return stack_mock
