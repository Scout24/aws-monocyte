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

import boto.s3
import boto.s3.bucket
import boto.exception
from unittest import TestCase
from mock import patch, Mock
from monocyte.handler import s3


class S3BucketTest(TestCase):

    def setUp(self):
        self.boto_mock = patch("monocyte.handler.s3.boto").start()
        self.bucket_mock = self._given_bucket_mock()
        self.s3_handler = s3.Bucket(lambda region_name: True)

    def tearDown(self):
        patch.stopall()

    def test_fetch_unwanted_resources(self):
        only_resource = list(self.s3_handler.fetch_unwanted_resources())[0]
        self.assertEquals(only_resource.wrapped, self.bucket_mock)

    @patch("monocyte.handler.s3.print", create=True)
    def test_fetch_unwanted_resources_400_exception(self, print_mock):
        self.bucket_mock.get_location.side_effect = boto.exception.S3ResponseError(400, 'boom')
        list(self.s3_handler.fetch_unwanted_resources())

        print_mock.assert_called_with('\twarning: get_location() crashed for test_bucket, skipping')

    def test_fetch_unwanted_resources_not_400_exception(self):
        self.bucket_mock.get_location.side_effect = boto.exception.S3ResponseError(999, 'boom')
        only_resource = list(self.s3_handler.fetch_unwanted_resources())[0]

        self.assertEquals(only_resource.region, '__error__')

    def test_fetch_unwanted_resources_set_default_region(self):
        self.bucket_mock.get_location.return_value = ""
        only_resource = list(self.s3_handler.fetch_unwanted_resources())[0]

        self.assertEquals(only_resource.region, s3.US_STANDARD_REGION)

    def test_to_string(self):
        only_resource = list(self.s3_handler.fetch_unwanted_resources())[0]
        resource_string = self.s3_handler.to_string(only_resource)

        self.assertTrue(only_resource.region in resource_string)
        self.assertTrue(self.bucket_mock.name in resource_string)
        self.assertTrue(self.bucket_mock.creation_date in resource_string)

    def _given_bucket_mock(self):
        bucket_mock = Mock(boto.s3.bucket.Bucket)
        bucket_mock.get_location.return_value = "my-stupid-region"
        bucket_mock.name = "test_bucket"
        bucket_mock.creation_date = "01.01.2015"

        self.boto_mock.connect_s3.return_value.get_all_buckets.return_value = [bucket_mock]
        return bucket_mock
