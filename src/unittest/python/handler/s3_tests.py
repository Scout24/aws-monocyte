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

import boto3
from moto import mock_s3
from mock import patch
from monocyte.handler import s3
import os
import unittest2

BUCKET_NAME = "test_bucket"

LOCATATION_CRASHED = "warning: get_location() crashed for test_bucket, skipping"
KEYS_OMITTED = " ... (2 keys omitted)"
KEY = "'test.txt'"
INITIATING_DELITION = "Initiating deletion sequence for %s."


@unittest2.skipIf('http_proxy' in os.environ, 'HTTP proxies confuse moto/boto')
class S3BucketNewTest(unittest2.TestCase):

    def setUp(self):
        self.logger_mock = patch("monocyte.handler.logging").start()
        self.s3_handler = s3.Bucket(lambda region_name: region_name not in [
            'cn-north-1', 'us-gov-west-1'])

    def tearDown(self):
        patch.stopall()

    @mock_s3
    def test_fetch_unwanted_resources_no_resources(self):
        resources = list(self.s3_handler.fetch_unwanted_resources())
        self.assertEqual(resources, [])

    @mock_s3
    def test_fetch_unwanted_resources_one_resource(self):
        self._given_bucket_mock('test-bucket', 'eu-west-1')
        resources = list(self.s3_handler.fetch_unwanted_resources())
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0].resource_id, 'test-bucket')

    @mock_s3
    def test_fetch_unwanted_resources_two_resources(self):
        self._given_bucket_mock('test-bucket', 'eu-west-1')
        self._given_bucket_mock('bucket-eu', 'eu-central-1')
        resources = list(self.s3_handler.fetch_unwanted_resources())
        self.assertEqual(len(resources), 2)
        bucket_names_in = set(['bucket-eu', 'test-bucket'])
        bucket_names_out = set([resource.resource_id for resource in
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
        bucket_names_out = set([resource.resource_id for resource in
                                resources])
        self.assertEqual(bucket_names_out, bucket_names_in)

    @mock_s3
    def test_bucket_to_string(self):
        self._given_bucket_mock('test-bucket', 'eu-central-1')
        resources = list(self.s3_handler.fetch_unwanted_resources())
        self.assertEqual(len(resources), 1)
        bucket_str = self.s3_handler.to_string(resources[0])
        # wrong region cause by moto. Therefore region not asserted.
        self.assertIn('test-bucket', bucket_str)

    @mock_s3
    def test_bucket_delete_dry_run(self):
        self._given_bucket_mock('test-bucket', 'eu-west-1')
        self.s3_handler.dry_run = True
        resources = list(self.s3_handler.fetch_unwanted_resources())
        self.assertEqual(len(resources), 1)
        self.s3_handler.delete(resources[0])
        resources = list(self.s3_handler.fetch_unwanted_resources())
        self.assertEqual(len(resources), 1)

    @unittest2.skip("https://github.com/spulec/moto/issues/734")
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
        client = boto3.client('s3', region_name=region_name)
        client.create_bucket(Bucket=bucket_name)
