from __future__ import print_function, absolute_import, division

import boto3
import unittest2
import random
from functools import wraps

from monocyte.handler import s3 as s3_handler


def region_filter(region_name):
    if region_name in ['cn-north-1', 'us-gov-west-1']:
        return False
    return True


class S3TestsBase(unittest2.TestCase):
    def setUp(self):
        self.s3_handler = s3_handler.Bucket(lambda region_name: region_name not in [
            'cn-north-1', 'us-gov-west-1'])
        self.prefix = 'test-' + hex(random.randint(0, 2**48))[2:] + '-'
        self.our_buckets = []

        def my_filter(old_function):
            @wraps(old_function)
            def new_function():
                return [resource for resource in old_function()
                        if resource.resource_id in self.our_buckets]

            return new_function

        self.s3_handler.fetch_unwanted_resources = my_filter(
            self.s3_handler.fetch_unwanted_resources
        )

    def tearDown(self):
        for bucket_name in self.our_buckets:
            self.s3_handler.dry_run = False
            self.s3_handler.delete(bucket_name)

    def connect_to_region(self, region_name):
        return boto3.client('s3', region_name=region_name)

    def _create_bucket(self, bucket_name, region_name, create_key=False):
        bucket_name = self.prefix + bucket_name
        client = self.connect_to_region(region_name)

        if region_name == 'us-east-1':
            client.create_bucket(Bucket=bucket_name)
        else:
            client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': region_name})
        self.our_buckets.append(bucket_name)

        if create_key:
            client.put_object(Bucket=bucket_name, Key='foobar')

    def run_single_test(self, bucket_name, region_name, create_key, dry_run):
        self.s3_handler.dry_run = dry_run
        self._create_bucket(bucket_name, region_name, create_key=create_key)

        resources = self.s3_handler.fetch_unwanted_resources()
        self.assertEqual(len(resources), 1)
        resource = resources[0]
        self.assertIn(bucket_name, resource.resource_id)
        self.assertIn(bucket_name, str(resource))
        self.assertIn(region_name, str(resource))

        self.s3_handler.delete(resources[0])

        resources = self.s3_handler.fetch_unwanted_resources()

        if dry_run:
            # In dry run, resources must not be deleted. So we should find the
            # same bucket again.
            self.assertEqual(len(resources), 1)
            self.assertIn(bucket_name, resources[0].resource_id)
        else:
            self.assertEqual(len(resources), 0)
            # Prevent self.tearDown() from failing with "404 Not Found".
            self.our_buckets = []
            return
