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

import boto.ec2
import boto.exception
import boto.ec2.regioninfo
import boto.ec2.instance
import boto.ec2.volume
from unittest import TestCase
from mock import patch, Mock
from monocyte.handler import ec2
from monocyte.handler import Resource

VOLUME_ID = "vol-12345"

INSTANCE_ID = "id-12345"


class EC2InstanceHandlerTest(TestCase):

    def setUp(self):
        self.ec2_mock = patch("monocyte.handler.ec2.ec2").start()
        self.positive_fake_region = Mock(boto.ec2.regioninfo.EC2RegionInfo)
        self.positive_fake_region.name = "allowed_region"
        self.negative_fake_region = Mock(boto.ec2.regioninfo.EC2RegionInfo)
        self.negative_fake_region.name = "forbidden_region"

        self.ec2_mock.regions.return_value = [self.positive_fake_region, self.negative_fake_region]
        self.logger_mock = patch("monocyte.handler.logging").start()
        self.ec2_handler = ec2.Instance(lambda region_name: region_name == self.positive_fake_region.name)

        self.instance_mock = self._given_instance_mock()

    def tearDown(self):
        patch.stopall()

    def test_fetch_unwanted_resources_filtered_by_region(self):
        only_resource = list(self.ec2_handler.fetch_unwanted_resources())[0]
        self.assertEquals(only_resource.wrapped, self.instance_mock)

    def test_fetch_unwanted_resources_filtered_by_ignored_resources(self):
        self.ec2_handler.ignored_resources = [INSTANCE_ID]
        empty_list = list(self.ec2_handler.fetch_unwanted_resources())
        self.assertEquals(empty_list.__len__(), 0)

    def test_to_string(self):
        only_resource = list(self.ec2_handler.fetch_unwanted_resources())[0]
        resource_string = self.ec2_handler.to_string(only_resource)

        self.assertTrue(self.instance_mock.id in resource_string)
        self.assertTrue(self.instance_mock.instance_type in resource_string)
        self.assertTrue(self.instance_mock.launch_time in resource_string)
        self.assertTrue(self.instance_mock.public_dns_name in resource_string)
        self.assertTrue(self.instance_mock.key_name in resource_string)
        self.assertTrue(self.instance_mock.region.name in resource_string)

    def test_delete(self):
        resource = Resource(self.instance_mock, self.negative_fake_region.name)
        connection = self.ec2_mock.connect_to_region.return_value

        e = boto.exception.EC2ResponseError(412, 'boom')
        e.message = "test"
        connection.terminate_instances.side_effect = e

        deleted_resource = self.ec2_handler.delete(resource)[0]

        self.assertEquals(self.instance_mock, deleted_resource)
        self.logger_mock.getLogger.return_value.info.assert_called_with("Termination test")

    def _given_instance_mock(self):
        instance_mock = Mock(boto.ec2.instance, image_id="ami-1112")
        instance_mock.id = INSTANCE_ID
        instance_mock.instance_type = "m1.small"
        instance_mock.launch_time = "01.01.2015"
        instance_mock.public_dns_name = "test.aws.com"
        instance_mock.key_name = "test-ssh-key"
        instance_mock.region = self.positive_fake_region
        instance_mock._state = boto.ec2.instance.InstanceState(16, "running")
        instance_mock.state = instance_mock._state.name

        self.ec2_mock.connect_to_region.return_value.get_only_instances.return_value = [instance_mock]
        return instance_mock


class EC2VolumeHandlerTest(TestCase):

    def setUp(self):
        self.ec2_mock = patch("monocyte.handler.ec2.ec2").start()
        self.positive_fake_region = Mock(boto.ec2.regioninfo.EC2RegionInfo)
        self.positive_fake_region.name = "allowed_region"
        self.negative_fake_region = Mock(boto.ec2.regioninfo.EC2RegionInfo)
        self.negative_fake_region.name = "forbidden_region"

        self.ec2_mock.regions.return_value = [self.positive_fake_region, self.negative_fake_region]
        self.logger_mock = patch("monocyte.handler.logging").start()
        self.ec2_handler = ec2.Volume(lambda region_name: region_name == self.positive_fake_region.name)

        self.volume_mock = self._given_volume_mock()

    def tearDown(self):
        patch.stopall()

    def test_fetch_unwanted_resources_filtered_by_region(self):
        only_resource = list(self.ec2_handler.fetch_unwanted_resources())[0]
        self.assertEquals(only_resource.wrapped, self.volume_mock)

    def test_fetch_unwanted_resources_filtered_by_ignored_resources(self):
        self.ec2_handler.ignored_resources = [VOLUME_ID]
        empty_list = list(self.ec2_handler.fetch_unwanted_resources())
        self.assertEquals(empty_list.__len__(), 0)

    def test_to_string(self):
        only_resource = list(self.ec2_handler.fetch_unwanted_resources())[0]
        resource_string = self.ec2_handler.to_string(only_resource)

        self.assertTrue(self.volume_mock.id in resource_string)
        self.assertTrue(self.volume_mock.create_time in resource_string)
        self.assertTrue(self.volume_mock.region.name in resource_string)

    def test_delete(self):
        resource = Resource(self.volume_mock, self.negative_fake_region.name)
        connection = self.ec2_mock.connect_to_region.return_value

        e = boto.exception.EC2ResponseError(412, 'boom')
        e.message = "test"
        connection.delete_volume.side_effect = e

        deleted_resource = self.ec2_handler.delete(resource)[0]

        self.assertEquals(self.volume_mock, deleted_resource)
        self.logger_mock.getLogger.return_value.info.assert_called_with("Termination test")

    def _given_volume_mock(self):
        volume_mock = Mock(boto.ec2.volume)
        volume_mock.id = VOLUME_ID
        volume_mock.create_time = "01.01.2015"
        volume_mock.region = self.positive_fake_region
        volume_mock.status = "OK"

        self.ec2_mock.connect_to_region.return_value.get_all_volumes.return_value = [volume_mock]
        return volume_mock
