from __future__ import print_function, absolute_import, division

import unittest2

from s3_tests_base import S3TestsBase


class S3DotnameTests(S3TestsBase):
    def test_run_all_tests(self):
        # eu-west-1 is just a normal region.
        # eu-central-1 is a region that only supports SigV4
        # us-east-1 is the default region. Buckets created there do not
        # have a location constraint.
        regions = ('eu-west-1', 'eu-central-1', 'us-east-1')
        decisions = (True, False)

        count = 0
        for region in regions:
            for create_key in decisions:
                for dry_run in decisions:
                    count += 1
                    bucket_name = "bucket" + str(count)
                    print("Testing with bucket_name=%s region=%s create_key=%s "
                          "dry_run=%s" % (bucket_name, region, create_key, dry_run))
                    self.setUp()
                    try:
                        self.run_single_test(bucket_name, region, create_key, dry_run)
                    finally:
                        self.tearDown()


if __name__ == "__main__":
    unittest2.main()
