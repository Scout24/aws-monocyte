import json
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
       self.client.delete_role(
           RoleName='integrationtest_role'
       )

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
        self.assertEqual(['integrationtest_role'], self._uniq(unwanted_resource))

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
        self.assertEqual(['monocyteIntegrationTest'], self._uniq(unwanted_resource))

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
        self.assertEqual(['monocyteIntegrationTest'], self._uniq(unwanted_resource))

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
