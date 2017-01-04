from __future__ import print_function, absolute_import, division

import unittest2

from s3_tests_base import S3TestsBase


class S3BucketToStringTests(S3TestsBase):
    def test_bucket_to_string_dry_run_no_sigv4(self):
        self._create_bucket('test-bucket10', 'eu-west-1')
        self.s3_handler.dry_run = True

        resources = self.s3_handler.fetch_unwanted_resources()
        self.assertEqual(len(resources), 1)

        bucket_str = self.s3_handler.to_string(resources[0])
        self.assertIn('test-bucket10', bucket_str)
        self.assertIn('eu-west-1', bucket_str)

    def test_bucket_to_string_dry_run_sigv4(self):
        self._create_bucket('test-bucket11', 'eu-central-1')
        self.s3_handler.dry_run = True

        resources = self.s3_handler.fetch_unwanted_resources()
        self.assertEqual(len(resources), 1)

        bucket_str = self.s3_handler.to_string(resources[0])
        self.assertIn('test-bucket11', bucket_str)
        self.assertIn('eu-central-1', bucket_str)

    def test_bucket_to_string_dry_run_sigv4_with_dot_name(self):
        self._create_bucket('test.bucket12', 'eu-central-1')
        self.s3_handler.dry_run = True

        resources = self.s3_handler.fetch_unwanted_resources()
        self.assertEqual(len(resources), 1)

        bucket_str = self.s3_handler.to_string(resources[0])
        self.assertIn('test.bucket12', bucket_str)
        self.assertIn('eu-central-1', bucket_str)


if __name__ == "__main__":
    unittest2.main()
