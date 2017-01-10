import logging

import boto3
import unittest2
from mock import MagicMock
from monocyte.handler import iam as iam_handler

class IamUserTests(unittest2.TestCase):
    def setUp(self):
        logging.captureWarnings(True)
        self.iam_handler = iam_handler.User(MagicMock)
        self.iam_handler.dry_run = True

    def _create_user(self, username):
        iam = boto3.client('iam')
        iam.create_user(UserName=username)

    def _delete_user(self, username):
        iam = boto3.client('iam')
        iam.delete_user(UserName=username)

    def _uniq(self, resources):
        uniq_names = []
        for resource in resources:
            name = resource.wrapped['UserName']
            if not name.startswith('integrationtest'):
                continue
            uniq_names.append(name)

        return uniq_names

    def test_no_user_no_unwanted_resource(self):
        resources = self.iam_handler.fetch_unwanted_resources()
        unwanted_users = self._uniq(resources)
        self.assertAlmostEqual([], unwanted_users)

    def test_one_user_found_one_created(self):
        resources = self.iam_handler.fetch_unwanted_resources()
        username = 'integrationtest_user_1'
        self._create_user(username)

        unwanted_users = self._uniq(resources)
        self._delete_user(username)

        self.assertEqual(['integrationtest_user_1'], unwanted_users)


if __name__ == "__main__":
    unittest2.main()
