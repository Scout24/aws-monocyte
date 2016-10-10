import logging
import time
import json
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


class IamAwsPolicyTests(unittest2.TestCase):
    def setUp(self):
        logging.captureWarnings(True)
        self.iam_handler = iam_handler.IamPolicy(MagicMock)
        self.iam_handler.dry_run = True

    def _create_policy(self, policy):
        iam = boto3.client('iam')
        policy_response = iam.create_policy(PolicyName='monocyteIntegrationTest', PolicyDocument=json.dumps(policy))
        return policy_response['Policy']['Arn']

    def _delete_policy(self, arn):
       iam = boto3.client('iam')
       iam.delete_policy(PolicyArn=arn)

    def _uniq(self, resources):
        uniq_names = []
        for resource in resources:
            name = resource.wrapped['PolicyName']
            if not name.startswith('monocyteIntegrationTest'):
                continue
            uniq_names.append(name)

        return uniq_names

    def test_right_policy_returns_no_failure(self):
        policy = {
            "Version": "2012-10-17",
            "Statement": {
                "Effect": "Allow",
                "Action": "s3:testaction",
                "Resource": "arn:aws:s3:::example_bucket"
            }
        }
        arn = self._create_policy(policy)

        unwanted_resource = self.iam_handler.fetch_unwanted_resources()
        self.assertEqual([], self._uniq(unwanted_resource))
        self._delete_policy(arn)

    def test_wildcard_policy_returns_failure(self):
        policy = {
            "Version": "2012-10-17",
            "Statement": {
                "Effect": "Allow",
                "Action": "*",
                "Resource": "arn:aws:s3:::example_bucket"
            }
        }
        arn = self._create_policy(policy)
        unwanted_resource = self.iam_handler.fetch_unwanted_resources()
        self.assertEqual(['monocyteIntegrationTest'], self._uniq(unwanted_resource))
        self._delete_policy(arn)


if __name__ == "__main__":
    unittest2.main()
