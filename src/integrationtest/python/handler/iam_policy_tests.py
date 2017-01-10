import json
import logging

import boto3
import unittest2
from mock import MagicMock
from monocyte.handler import iam as iam_handler


class IamAPolicyTests(unittest2.TestCase):
    def setUp(self):
        self.arn = ''
        logging.captureWarnings(True)
        self.iam_handler = iam_handler.IamPolicy(MagicMock)
        self.iam_handler.dry_run = True

    def tearDown(self):
        self._delete_policy(self.arn)

    def _create_policy(self, policy):
        iam = boto3.client('iam')
        policy_response = iam.create_policy(
            PolicyName='monocyteIntegrationTest',
            PolicyDocument=json.dumps(policy))
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
        self.arn = self._create_policy(policy)

        unwanted_resource = self.iam_handler.fetch_unwanted_resources()
        self.assertEqual([], self._uniq(unwanted_resource))

    def test_action_wildcard_policy_returns_failure(self):
        policy = {
            "Version": "2012-10-17",
            "Statement": {
                "Effect": "Allow",
                "Action": "*",
                "Resource": "arn:aws:s3:::example_bucket"
            }
        }
        self.arn = self._create_policy(policy)
        unwanted_resource = self.iam_handler.fetch_unwanted_resources()
        self.assertEqual(['monocyteIntegrationTest'], self._uniq(unwanted_resource))

    def test_resource_wildcard_with_elb_policy_returns_no_failure(self):
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "elasticloadbalancing:*"
                    ],
                    "Resource": "*"
                }
            ]
        }
        self.arn = self._create_policy(policy)
        unwanted_resource = self.iam_handler.fetch_unwanted_resources()
        self.assertEqual([], self._uniq(unwanted_resource))

    def test_resource_only_wildcard_with_returns_failure(self):
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:*"
                    ],
                    "Resource": "*"
                }
            ]
        }
        self.arn = self._create_policy(policy)
        unwanted_resource = self.iam_handler.fetch_unwanted_resources()
        self.assertEqual([], self._uniq(unwanted_resource))

    def test_resource_only_wildcard_list_returns_failure(self):
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:*"
                    ],
                    "Resource": ["*"]
                }
            ]
        }
        self.arn = self._create_policy(policy)
        unwanted_resource = self.iam_handler.fetch_unwanted_resources()
        self.assertEqual([], self._uniq(unwanted_resource))

    def test_action_with_wildcard_returns_no_failure(self):
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "s3:*",
                    "Resource": "arn:aws:s3:::example_bucket"
                }
            ]
        }
        self.arn = self._create_policy(policy)
        unwanted_resource = self.iam_handler.fetch_unwanted_resources()
        self.assertEqual([], self._uniq(unwanted_resource))

    def test_action_with_wildcard_returns_failure(self):
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "*",
                    "Resource": "arn:aws:s3:::example_bucket"
                }
            ]
        }
        self.arn = self._create_policy(policy)
        unwanted_resource = self.iam_handler.fetch_unwanted_resources()
        self.assertEqual(['monocyteIntegrationTest'], self._uniq(unwanted_resource))

    def test_wildcards_returns_failure(self):
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "*",
                    "Resource": "*"
                }
            ]
        }
        self.arn = self._create_policy(policy)
        unwanted_resource = self.iam_handler.fetch_unwanted_resources()
        self.assertEqual(['monocyteIntegrationTest'], self._uniq(unwanted_resource))

    def test_wildcards_as_list_returns_failure(self):
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["*"],
                    "Resource": ["*"]
                }
            ]
        }
        self.arn = self._create_policy(policy)
        unwanted_resource = self.iam_handler.fetch_unwanted_resources()
        self.assertEqual(['monocyteIntegrationTest'], self._uniq(unwanted_resource))


if __name__ == "__main__":
    unittest2.main()
