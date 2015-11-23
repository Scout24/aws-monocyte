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

import boto.s3
import boto.s3.bucket
import boto.s3.key
from boto.s3.connection import OrdinaryCallingFormat, SubdomainCallingFormat
import boto.exception
import boto.regioninfo
from moto import mock_s3
from mock import patch, Mock, MagicMock
from monocyte.handler import s3, Resource
import unittest2

BUCKET_NAME = "test_bucket"

LOCATATION_CRASHED = "warning: get_location() crashed for test_bucket, skipping"
KEYS_OMITTED = " ... (2 keys omitted)"
KEY = "'test.txt'"
INITIATING_DELITION = "Initiating deletion sequence for %s."


@unittest2.skip
class S3BucketTest(unittest2.TestCase):

    def setUp(self):
        self.boto_mock = patch("monocyte.handler.s3.boto").start()
        self.bucket_mock = self._given_bucket_mock()
        self.key_mock = self._given_key_mock()
        self.resource_type = "s3 Bucket"
        self.negative_fake_region = Mock(boto.regioninfo.RegionInfo)
        self.negative_fake_region.name = "forbidden_region"
        self.logger_mock = patch("monocyte.handler.logging").start()
        self.s3_handler = s3.Bucket(lambda region_name: True)

    def tearDown(self):
        patch.stopall()

    def test_fetch_unwanted_resources_400_exception(self):
        self.bucket_mock.get_location.side_effect = boto.exception.S3ResponseError(400, 'boom')
        list(self.s3_handler.fetch_unwanted_resources())

        self.logger_mock.getLogger.return_value.error.assert_called_with(LOCATATION_CRASHED)

    def test_fetch_unwanted_resources_not_400_exception(self):
        self.bucket_mock.get_location.side_effect = boto.exception.S3ResponseError(999, 'boom')
        only_resource = list(self.s3_handler.fetch_unwanted_resources())[0]

        self.assertEqual(only_resource.region, '__error__')

    def test_fetch_unwanted_resources_set_default_region(self):
        self.bucket_mock.get_location.return_value = ""
        only_resource = list(self.s3_handler.fetch_unwanted_resources())[0]

        self.assertEqual(only_resource.region, s3.US_STANDARD_REGION)

    @patch('monocyte.handler.s3.Bucket.apply_bucket_function')
    def test_to_string(self, mock_apply_bucket_function):
        mock_apply_bucket_function.return_value = [self.key_mock]
        only_resource = list(self.s3_handler.fetch_unwanted_resources())[0]
        resource_string = self.s3_handler.to_string(only_resource)

        self.assertTrue(only_resource.region in resource_string)
        self.assertTrue(self.bucket_mock.name in resource_string)
        self.assertTrue(self.bucket_mock.creation_date in resource_string)

    def test_fetch_unwanted_resources_filtered_by_ignored_resources(self):
        self.s3_handler.ignored_resources = [BUCKET_NAME]
        empty_list = list(self.s3_handler.fetch_unwanted_resources())
        self.assertEqual(empty_list, [])

    def test_skip_deletion_in_dry_run_with_keys(self):
        self.s3_handler.dry_run = True
        self.bucket_mock.get_all_keys.return_value = [self.key_mock]
        self.bucket_mock.list.return_value = [self.key_mock]
        resource = Resource(self.bucket_mock, self.resource_type, self.bucket_mock.name,
                            self.bucket_mock.creation_date, self.negative_fake_region.name)
        self.s3_handler.delete(resource)
        call_args = self.logger_mock.getLogger.return_value.info.call_args[0][0]
        self.assertTrue(KEY in call_args)

    def test_skip_deletion_in_dry_run_with_keys_omitted(self):
        self.s3_handler.dry_run = True
        self.bucket_mock.get_all_keys.return_value = [self.key_mock] * 6
        self.bucket_mock.list.return_value = [self.key_mock] * 6
        resource = Resource(self.bucket_mock, self.resource_type, self.bucket_mock.name,
                            self.bucket_mock.creation_date, self.negative_fake_region.name)
        self.s3_handler.delete(resource)
        call_args = self.logger_mock.getLogger.return_value.info.call_args[0][0]
        self.assertTrue(KEYS_OMITTED in call_args)

    @patch('monocyte.handler.s3.Bucket.apply_bucket_function')
    @patch('monocyte.handler.s3.Bucket.apply_s3_function')
    def test_does_delete_if_not_dry_run(self, mock_apply_s3_function,
                                        mock_apply_bucket_function):
        self.s3_handler.dry_run = False
        resource = Resource(self.bucket_mock, self.resource_type, self.bucket_mock.name,
                            self.bucket_mock.creation_date, self.negative_fake_region.name)

        mock_apply_bucket_function.return_value = [self.key_mock]
        mock_apply_s3_function.return_value = [self.bucket_mock]
        # self.bucket_mock.delete_keys.return_value = [self.key_mock]
        # self.boto_mock.connect_s3().delete_bucket.return_value = [
        # self.bucket_mock]
        self.s3_handler.delete(resource)

    def _given_bucket_mock(self):
        bucket_mock = MagicMock(boto.s3.bucket.Bucket)
        bucket_mock.get_location.return_value = "my-region"
        bucket_mock.name = BUCKET_NAME
        bucket_mock.creation_date = "01.01.2015"

        self.boto_mock.connect_s3.return_value.get_all_buckets.return_value = [bucket_mock]
        return bucket_mock

    def _given_key_mock(self):
        key_mock = Mock(boto.s3.key.Key)
        key_mock.name = "test.txt"

        self.boto_mock.connect_s3.return_value.get_all_keys.return_value = [key_mock]
        return key_mock


class S3BucketNewTest(unittest2.TestCase):

    def setUp(self):
        # self.boto_mock = patch("monocyte.handler.s3.boto").start()
        # self.key_mock = self._given_key_mock()
        # self.resource_type = "s3 Bucket"
        # self.negative_fake_region = Mock(boto.regioninfo.RegionInfo)
        # self.negative_fake_region.name = "forbidden_region"
        self.logger_mock = patch("monocyte.handler.logging").start()
        self.s3_handler = s3.Bucket(lambda region_name: region_name not in [
            'cn-north-1', 'us-gov-west-1'])

    def tearDown(self):
        patch.stopall()

    @mock_s3
    def test_connect_to_region_non_sigv4_regions(self):
        for region in ['eu-west-1']:
            conn = self.s3_handler.connect_to_region(region)
            self.assertIn(region, conn.host)
            self.assertIsInstance(conn.calling_format, SubdomainCallingFormat)
            self.assertEqual(conn.get_all_buckets(), [])


    @mock_s3
    def test_connect_to_region_sigv4_region_eu_central_1(self):
        conn = self.s3_handler.connect_to_region('eu-central-1')
        self.assertIn('eu-central-1', conn.host)
        self.assertIsInstance(conn.calling_format, SubdomainCallingFormat)
        self.assertEqual(conn.get_all_buckets(), [])

    @mock_s3
    def test_connect_to_region_non_sigv4_regions_with_bucket_name(self):
        bucket_name = 'test.foo.bar'
        for region in ['eu-west-1']:
            conn = self.s3_handler.connect_to_region(region, bucket_name)
            self.assertIn(region, conn.host)
            self.assertIsInstance(conn.calling_format, OrdinaryCallingFormat)
            self.assertEqual(conn.get_all_buckets(), [])

    @mock_s3
    def test_connect_to_region_sigv4_region_eu_central_1_with_bucket_name(self):
        conn = self.s3_handler.connect_to_region('eu-central-1', 'test.foo.bar')
        self.assertIsInstance(conn.calling_format, OrdinaryCallingFormat)
        self.assertIn('eu-central-1', conn.host)
        self.assertEqual(conn.get_all_buckets(), [])

    @mock_s3
    def test_fetch_unwanted_resources_no_resources(self):
        # self.bucket_mock = self._given_bucket_mock()
        resources = list(self.s3_handler.fetch_unwanted_resources())
        self.assertEqual(resources, [])

    @mock_s3
    def test_fetch_unwanted_resources_one_resource(self):
        bucket_mock = self._given_bucket_mock('test-bucket', 'eu-west-1')
        resources = list(self.s3_handler.fetch_unwanted_resources())
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0].wrapped.name, bucket_mock.name)

    @mock_s3
    def test_fetch_unwanted_resources_two_resources(self):
        self._given_bucket_mock('test-bucket', 'eu-west-1')
        self._given_bucket_mock('bucket-eu', 'eu-central-1')
        resources = list(self.s3_handler.fetch_unwanted_resources())
        self.assertEqual(len(resources), 2)
        bucket_names_in = set(['bucket-eu', 'test-bucket'])
        bucket_names_out = set([resource.wrapped.name for resource in
                                resources])
        self.assertEqual(bucket_names_out, bucket_names_in)

    @mock_s3
    def test_fetch_unwanted_resources_three_resources(self):
        self._given_bucket_mock('test.ap-bucket', 'ap-southeast-1')
        self._given_bucket_mock('test.bucket', 'us-east-1')
        self._given_bucket_mock('bucket.eu', 'eu-central-1')
        resources = list(self.s3_handler.fetch_unwanted_resources())
        self.assertEqual(len(resources), 3)
        bucket_names_in = set(['bucket.eu', 'test.bucket', 'test.ap-bucket'])
        bucket_names_out = set([resource.wrapped.name for resource in
                                resources])
        self.assertEqual(bucket_names_out, bucket_names_in)

    @mock_s3
    def test_bucket_to_string(self):
        self._given_bucket_mock('test-bucket', 'eu-central-1')
        resources = list(self.s3_handler.fetch_unwanted_resources())
        self.assertEqual(len(resources), 1)
        bucket_str = self.s3_handler.to_string(resources[0])
        self.assertIn('test-bucket', bucket_str)
        self.assertIn('us-east-1', bucket_str)

    @mock_s3
    def test_bucket_delete_dry_run(self):
        self._given_bucket_mock('test-bucket', 'eu-west-1')
        self.s3_handler.dry_run = True
        resources = list(self.s3_handler.fetch_unwanted_resources())
        self.assertEqual(len(resources), 1)
        self.s3_handler.delete(resources[0])
        resources = list(self.s3_handler.fetch_unwanted_resources())
        self.assertEqual(len(resources), 1)

    @mock_s3
    def test_bucket_delete_no_dry_run(self):
        self._given_bucket_mock('test-bucket', 'eu-west-1')
        self.s3_handler.dry_run = False
        resources = list(self.s3_handler.fetch_unwanted_resources())
        self.assertEqual(len(resources), 1)
        self.s3_handler.delete(resources[0])
        resources = list(self.s3_handler.fetch_unwanted_resources())
        self.assertEqual(len(resources), 0)

    def _given_bucket_mock(self, bucket_name, region_name):
        conn = self.s3_handler.connect_to_region(region_name)
        return conn.create_bucket(bucket_name, location=region_name)
