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

import boto.cloudformation
import boto.cloudformation.stack

from unittest import TestCase
from mock import patch, Mock

from monocyte.handler import cloudformation
from monocyte.handler import Resource

STACK_NAME = 'test-stack'

DELETION_STATEMENT = "Initiating deletion sequence for %s."
VALID_TARGET_STATE_STATEMENT = "Skipping deletion: State 'DELETE_COMPLETE' is a valid target state."


class CloudFormationTest(TestCase):

    def setUp(self):
        self.cloudformation_mock = patch("monocyte.handler.cloudformation.cloudformation").start()
        self.positive_fake_region = Mock(boto.cloudformation.regions)
        self.positive_fake_region.name = "allowed_region"
        self.negative_fake_region = Mock(boto.cloudformation.regions)
        self.negative_fake_region.name = "forbbiden_region"
        self.resource_type = "cloudformation Stack"
        self.cloudformation_mock.regions.return_value = [self.positive_fake_region, self.negative_fake_region]
        self.logger_mock = patch("monocyte.handler.logging").start()
        self.cloudformation_handler = cloudformation.Stack(
            lambda region_name: region_name == self.positive_fake_region.name)

        self.stack_mock = self._given_stack_mock()

    def tearDown(self):
        patch.stopall()

    def test_fetch_unwanted_resources_filtered_by_region(self):
        only_resource = list(self.cloudformation_handler.fetch_unwanted_resources())[0]
        self.assertEquals(only_resource.wrapped, self.stack_mock)

    def test_fetch_unwanted_resources_filtered_by_ignored_resources(self):
        self.cloudformation_handler.ignored_resources = [STACK_NAME]
        empty_list = list(self.cloudformation_handler.fetch_unwanted_resources())
        self.assertEquals(empty_list.__len__(), 0)

    def test_to_string(self):
        only_resource = list(self.cloudformation_handler.fetch_unwanted_resources())[0]
        resource_string = self.cloudformation_handler.to_string(only_resource)

        self.assertTrue(self.stack_mock.stack_status in resource_string)
        self.assertTrue(self.stack_mock.creation_time in resource_string)
        self.assertTrue(self.stack_mock.region in resource_string)

    def test_skip_deletion_in_dry_run(self):
        resource = Resource(self.stack_mock, self.resource_type, self.stack_mock.stack_id,
                            self.stack_mock.creation_time, self.negative_fake_region.name)
        self.cloudformation_handler.dry_run = True
        self.cloudformation_handler.delete(resource)
        self.assertFalse(self.cloudformation_mock.connect_to_region.return_value.delete_stack.called)

    def test_does_delete_if_not_dry_run(self):
        resource = Resource(self.stack_mock, self.resource_type, self.stack_mock.stack_id,
                            self.stack_mock.creation_time, self.negative_fake_region.name)
        self.cloudformation_handler.dry_run = False
        self.cloudformation_handler.delete(resource)
        self.logger_mock.getLogger.return_value.info.assert_called_with(DELETION_STATEMENT % self.stack_mock.stack_name)
        self.assertTrue(self.cloudformation_mock.connect_to_region.return_value.delete_stack.called)

    def test_skip_deletion_if_already_deleted(self):
        self.stack_mock.stack_status = "DELETE_COMPLETE"
        resource = Resource(self.stack_mock, self.resource_type, self.stack_mock.stack_id,
                            self.stack_mock.creation_time, self.negative_fake_region.name)
        self.cloudformation_handler.dry_run = False
        self.assertRaises(Warning, self.cloudformation_handler.delete, resource)
        self.assertFalse(self.cloudformation_mock.connect_to_region.return_value.delete_stack.called)

    def _given_stack_mock(self):
        stack_mock = Mock(boto.cloudformation.stack.Stack, stack_name=STACK_NAME)
        stack_mock.stack_id = "id-12345"
        stack_mock.stack_status = "CREATE_COMPLETE"
        stack_mock.creation_time = "01.01.2015"
        stack_mock.region = self.positive_fake_region.name

        self.cloudformation_mock.connect_to_region.return_value.valid_states = ('CREATE_COMPLETE',
                                                                                'DELETE_COMPLETE')
        self.cloudformation_mock.connect_to_region.return_value.list_stacks.return_value = [stack_mock]
        return stack_mock
