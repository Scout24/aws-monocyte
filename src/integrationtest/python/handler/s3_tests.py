import unittest2
import random
from functools import wraps
from monocyte.handler import s3 as s3_handler
from monocyte.handler import Resource


class S3Tests(unittest2.TestCase):

    def setUp(self):
        self.s3_handler = s3_handler.Bucket(lambda region_name: region_name not in [
            'cn-north-1', 'us-gov-west-1'])
        self.prefix = 'test-' + hex(random.randint(0, 2**48))[2:] + '-'
        self.our_buckets = []

        def my_filter(old_function):
            @wraps(old_function)
            def new_function(*args):
                conn, bucket, checked_buckets = args
                if not bucket.name.startswith(self.prefix):
                    # print("skipping bucket {0}".format(bucket.name))
                    return
                else:
                    print("processing {0}".format(bucket.name))
                checked_buckets = []
                return old_function(conn, bucket, checked_buckets)

            return new_function

        self.s3_handler.check_if_unwanted_resource = my_filter(
            self.s3_handler.check_if_unwanted_resource
        )

    def tearDown(self):
        for resource in self.our_buckets:
            print("to be deleted {0}".format(resource.wrapped.name))
            self.s3_handler.dry_run = False
            self.s3_handler.delete(resource)

    def test_search_unwanted_resources_dry_run(self):
        self._create_bucket('test-bucket1', 'eu-west-1')
        self.s3_handler.dry_run = True

        resources = self.s3_handler.fetch_unwanted_resources()
        uniq_resources = self._uniq(resources)
        self.assertEqual(len(uniq_resources), 1)

        self.s3_handler.delete(uniq_resources[0])

        resources = self.s3_handler.fetch_unwanted_resources()
        uniq_resources = self._uniq(resources)
        self.assertEqual(len(uniq_resources), 1)

    def test_search_unwanted_resources_dry_run_with_key(self):
        self._create_bucket('test-bucket2', 'eu-west-1', create_key=True)
        self.s3_handler.dry_run = True

        resources = self.s3_handler.fetch_unwanted_resources()
        uniq_resources = self._uniq(resources)
        self.assertEqual(len(uniq_resources), 1)
        conn = self.s3_handler.connect_to_region(uniq_resources[0].region,
                                                 uniq_resources[0].wrapped.name)
        bucket = conn.get_bucket(uniq_resources[0].wrapped.name)
        all_keys = bucket.get_all_keys()
        self.assertEqual(len(all_keys), 1)

        self.s3_handler.delete(uniq_resources[0])

        resources = self.s3_handler.fetch_unwanted_resources()
        uniq_resources = self._uniq(resources)
        self.assertEqual(len(uniq_resources), 1)

    def test_search_unwanted_resources_dry_run_with_dot_name(self):
        self._create_bucket('test.bucket3', 'eu-west-1')
        self.s3_handler.dry_run = True

        resources = self.s3_handler.fetch_unwanted_resources()
        uniq_resources = self._uniq(resources)
        self.assertEqual(len(uniq_resources), 1)

        self.s3_handler.delete(uniq_resources[0])

        resources = self.s3_handler.fetch_unwanted_resources()
        uniq_resources = self._uniq(resources)
        self.assertEqual(len(uniq_resources), 1)

    def test_search_unwanted_resources_dry_run_with_dot_name_with_key(self):
        self._create_bucket('test.bucket3', 'eu-west-1', create_key=True)
        self.s3_handler.dry_run = True

        resources = self.s3_handler.fetch_unwanted_resources()
        uniq_resources = self._uniq(resources)
        self.assertEqual(len(uniq_resources), 1)
        conn = self.s3_handler.connect_to_region(uniq_resources[0].region,
                                                 uniq_resources[0].wrapped.name)
        bucket = conn.get_bucket(uniq_resources[0].wrapped.name)
        all_keys = bucket.get_all_keys()
        self.assertEqual(len(all_keys), 1)

        self.s3_handler.delete(uniq_resources[0])

        resources = self.s3_handler.fetch_unwanted_resources()
        uniq_resources = self._uniq(resources)
        self.assertEqual(len(uniq_resources), 1)

    def test_search_unwanted_resources_dry_run_sigv4(self):
        self._create_bucket('test-bucket4', 'eu-central-1')
        self.s3_handler.dry_run = True

        resources = self.s3_handler.fetch_unwanted_resources()
        uniq_resources = self._uniq(resources)
        self.assertEqual(len(uniq_resources), 1)

        self.s3_handler.delete(uniq_resources[0])

        resources = self.s3_handler.fetch_unwanted_resources()
        uniq_resources = self._uniq(resources)
        self.assertEqual(len(uniq_resources), 1)

    def test_search_unwanted_resources_dry_run_sigv4_with_key(self):
        self._create_bucket('test-bucket4', 'eu-central-1', create_key=True)
        self.s3_handler.dry_run = True

        resources = self.s3_handler.fetch_unwanted_resources()
        uniq_resources = self._uniq(resources)
        self.assertEqual(len(uniq_resources), 1)
        conn = self.s3_handler.connect_to_region(uniq_resources[0].region,
                                                 uniq_resources[0].wrapped.name)
        bucket = conn.get_bucket(uniq_resources[0].wrapped.name)
        all_keys = bucket.get_all_keys()
        self.assertEqual(len(all_keys), 1)

        self.s3_handler.delete(uniq_resources[0])

        resources = self.s3_handler.fetch_unwanted_resources()
        uniq_resources = self._uniq(resources)
        self.assertEqual(len(uniq_resources), 1)


    def test_search_unwanted_resources_dry_run_with_dot_name_sigv4(self):
        self._create_bucket('test.bucket5', 'eu-central-1')
        self.s3_handler.dry_run = True

        resources = self.s3_handler.fetch_unwanted_resources()
        uniq_resources = self._uniq(resources)
        self.assertEqual(len(uniq_resources), 1)

        self.s3_handler.delete(uniq_resources[0])

        resources = self.s3_handler.fetch_unwanted_resources()
        uniq_resources = self._uniq(resources)
        self.assertEqual(len(uniq_resources), 1)

    def test_search_unwanted_resources_no_dry_run_with_dot_name_sigv4_with_key(
            self):
        self.s3_handler.dry_run = False
        self._create_bucket('test.bucket6', 'eu-central-1', create_key=True)

        resources = self.s3_handler.fetch_unwanted_resources()
        uniq_resources = self._uniq(resources)
        self.assertEqual(len(uniq_resources), 1)
        conn = self.s3_handler.connect_to_region(uniq_resources[0].region,
                                                 uniq_resources[0].wrapped.name)
        bucket = conn.get_bucket(uniq_resources[0].wrapped.name)
        all_keys = bucket.get_all_keys()
        self.assertEqual(len(all_keys), 1)

        self.s3_handler.delete(uniq_resources[0])

        resources = self.s3_handler.fetch_unwanted_resources()
        uniq_resources = self._uniq(resources)
        self.assertEqual(len(uniq_resources), 0)

        # Prevent self.tearDown() from failing with "404 Not Found".
        self.our_buckets = []

    def test_search_unwanted_resources_dry_run_with_dot_name_default_region(self):
        self._create_bucket('test.bucket7', 'us-east-1')
        self.s3_handler.dry_run = True

        resources = self.s3_handler.fetch_unwanted_resources()
        uniq_resources = self._uniq(resources)
        self.assertEqual(len(uniq_resources), 1)

        self.s3_handler.delete(uniq_resources[0])

        resources = self.s3_handler.fetch_unwanted_resources()
        uniq_resources = self._uniq(resources)
        self.assertEqual(len(uniq_resources), 1)

    def test_search_unwanted_resources_dry_run_with_dot_name_default_region_with_key(self):
        self._create_bucket('test.bucket7', 'us-east-1', create_key=True)
        self.s3_handler.dry_run = True

        resources = self.s3_handler.fetch_unwanted_resources()
        uniq_resources = self._uniq(resources)
        self.assertEqual(len(uniq_resources), 1)
        conn = self.s3_handler.connect_to_region(uniq_resources[0].region,
                                                 uniq_resources[0].wrapped.name)
        bucket = conn.get_bucket(uniq_resources[0].wrapped.name)
        all_keys = bucket.get_all_keys()
        self.assertEqual(len(all_keys), 1)

        self.s3_handler.delete(uniq_resources[0])

        resources = self.s3_handler.fetch_unwanted_resources()
        uniq_resources = self._uniq(resources)
        self.assertEqual(len(uniq_resources), 1)

    def test_search_unwanted_resources_no_dry_run(self):
        self.s3_handler.dry_run = False
        self._create_bucket('test-bucket8', 'eu-west-1', create_key=False)

        resources = self.s3_handler.fetch_unwanted_resources()
        uniq_resources = self._uniq(resources)
        self.assertEqual(len(uniq_resources), 1)

        self.s3_handler.delete(uniq_resources[0])

        resources = self.s3_handler.fetch_unwanted_resources()
        uniq_resources = self._uniq(resources)
        self.assertEqual(len(uniq_resources), 0)

        # Prevent self.tearDown() from failing with "404 Not Found".
        self.our_buckets = []

    def test_search_unwanted_resources_no_dry_run_with_key(self):
        self.s3_handler.dry_run = False
        self._create_bucket('test-bucket9', 'eu-west-1', create_key=True)

        resources = self.s3_handler.fetch_unwanted_resources()
        uniq_resources = self._uniq(resources)
        self.assertEqual(len(uniq_resources), 1)
        conn = self.s3_handler.connect_to_region(uniq_resources[0].region,
                                                 uniq_resources[0].wrapped.name)
        bucket = conn.get_bucket(uniq_resources[0].wrapped.name)
        all_keys = bucket.get_all_keys()
        self.assertEqual(len(all_keys), 1)

        self.s3_handler.delete(uniq_resources[0])

        resources = self.s3_handler.fetch_unwanted_resources()
        uniq_resources = self._uniq(resources)
        self.assertEqual(len(uniq_resources), 0)

        # Prevent self.tearDown() from failing with "404 Not Found".
        self.our_buckets = []

    def test_bucket_to_string_dry_run_no_sigv4(self):
        self._create_bucket('test-bucket10', 'eu-west-1')
        self.s3_handler.dry_run = True

        resources = self.s3_handler.fetch_unwanted_resources()
        uniq_resources = self._uniq(resources)
        self.assertEqual(len(uniq_resources), 1)

        bucket_str = self.s3_handler.to_string(uniq_resources[0])
        self.assertIn('test-bucket10', bucket_str)
        self.assertIn('eu-west-1', bucket_str)

    def test_bucket_to_string_dry_run_sigv4(self):
        self._create_bucket('test-bucket11', 'eu-central-1')
        self.s3_handler.dry_run = True

        resources = self.s3_handler.fetch_unwanted_resources()
        uniq_resources = self._uniq(resources)
        self.assertEqual(len(uniq_resources), 1)

        bucket_str = self.s3_handler.to_string(uniq_resources[0])
        self.assertIn('test-bucket11', bucket_str)
        self.assertIn('eu-central-1', bucket_str)

    def test_bucket_to_string_dry_run_sigv4_with_dot_name(self):
        self._create_bucket('test.bucket12', 'eu-central-1')
        self.s3_handler.dry_run = True

        resources = self.s3_handler.fetch_unwanted_resources()
        uniq_resources = self._uniq(resources)
        self.assertEqual(len(uniq_resources), 1)

        bucket_str = self.s3_handler.to_string(uniq_resources[0])
        self.assertIn('test.bucket12', bucket_str)
        self.assertIn('eu-central-1', bucket_str)

    def _create_bucket(self, bucket_name, region_name, create_key=False):
        conn = self.s3_handler.connect_to_region(region_name)
        if region_name == 'us-east-1':
            bucket = conn.create_bucket(self.prefix + bucket_name)
        else:
            bucket = conn.create_bucket(self.prefix + bucket_name,
                                        location=region_name)
        resource = Resource(resource=bucket,
                            resource_type='s3.Bucket',
                            resource_id='42',
                            creation_date='2015-11-23',
                            region=self.s3_handler.map_location(
                                region_name))
        self.our_buckets.append(resource)
        if create_key:
            key = bucket.new_key(key_name='mytestkey')
            key.set_contents_from_string('test')
        return bucket

    def _uniq(self, resources):
        found_names = []
        uniq_resources = []
        for resource in resources:
            name = resource.wrapped.name
            if name in found_names:
                continue
            uniq_resources.append(resource)
            found_names.append(name)

        return uniq_resources


if __name__ == "__main__":
    unittest2.main()
