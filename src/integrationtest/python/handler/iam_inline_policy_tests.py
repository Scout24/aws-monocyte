import json
import logging

import boto3
import unittest2
from mock import MagicMock
from monocyte.handler import iam as iam_handler


class IamInlinePolicyTests(unittest2.TestCase):
    def setUp(self):
        self.arn = ''
        logging.captureWarnings(True)
        self.iam_handler = iam_handler.InlinePolicy(MagicMock)
        self.iam_handler.dry_run = True
        self.client = boto3.client('iam')

    def _create_role(self):
        assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        self.client.create_role(
            Path='/',
            RoleName='integrationtest_role',
            AssumeRolePolicyDocument=json.dumps(assume_role_policy)
        )

    def _put_inline_role_policy(self, inline_policy):
        self.client.put_role_policy(
            RoleName='integrationtest_role',
            PolicyName='integrationtest_inline_policy',
            PolicyDocument=json.dumps(inline_policy)
        )

    def _delete_inline_role_policy(self):
        self.client.delete_role_policy(
            RoleName='integrationtest_role',
            PolicyName='integrationtest_inline_policy'
        )

    def _delete_role(self):
        self.client.delete_role(RoleName='integrationtest_role')

    def tearDown(self):
        self._delete_inline_role_policy()
        self._delete_role()

    def _uniq(self, resources):
        uniq_names = []
        for resource in resources:
            name = resource.wrapped['RoleName']
            if not name.startswith('integrationtest_role'):
                continue
            uniq_names.append(name)

        return uniq_names

    def test_wildcard_in_inline_policy_action(self):
        self._create_role()
        inline_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "*"
                    ],
                    "Resource": "arn:aws:s3:::example_bucket"
                }
            ]
        }
        self._put_inline_role_policy(inline_policy)
        unwanted_resource = self.iam_handler.fetch_unwanted_resources()
        self.assertEqual(['integrationtest_role'], self._uniq(unwanted_resource))

    def test_no_wildcard_in_inline_policy(self):
        self._create_role()
        inline_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:read"
                    ],
                    "Resource": "arn:aws:s3:::example_bucket"
                }
            ]
        }
        self._put_inline_role_policy(inline_policy)
        unwanted_resource = self.iam_handler.fetch_unwanted_resources()
        self.assertEqual([], self._uniq(unwanted_resource))

    def test_wildcard_in_inline_policy_resource(self):
        self._create_role()
        inline_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "S3:read"
                    ],
                    "Resource": "*"
                }
            ]
        }
        self._put_inline_role_policy(inline_policy)
        unwanted_resource = self.iam_handler.fetch_unwanted_resources()
        self.assertEqual([], self._uniq(unwanted_resource))

    def test_wildcard_in_inline_policy_resource_and_action(self):
        self._create_role()
        inline_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "*"
                    ],
                    "Resource": "*"
                }
            ]
        }
        self._put_inline_role_policy(inline_policy)
        unwanted_resource = self.iam_handler.fetch_unwanted_resources()
        self.assertEqual(['integrationtest_role'], self._uniq(unwanted_resource))


if __name__ == "__main__":
    unittest2.main()
