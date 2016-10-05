from __future__ import print_function, absolute_import, division

import os
import unittest2
from monocyte.handler import Resource
from mock import patch, MagicMock
from monocyte.handler.iam import User
from monocyte.handler.iam import IamPolicy

os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['no_proxy'] = ''


class AwsIamUserHandlerTest(unittest2.TestCase):

    def setUp(self):
        def mock_region_filter(ignore):
            return True
        self.user_handler = User(mock_region_filter)
        self.boto3Mock = patch("monocyte.handler.iam.boto3").start()
        self.iamMock = MagicMock()
        self.iamMock.list_users.return_value = {'Users': []}
        self.boto3Mock.client.return_value = self.iamMock
        self.user_arn = 'arn:aws:iam::123456789:user/test1'
        self.user = {
            'UserName': 'test1',
            'Arn': 'arn:aws:iam::123456789:user/test1',
            'CreateDate': '2016-11-29'
        }

        self.iamMock.list_users.return_value = {'Users': [self.user]}

        def mock_whitelist():
            return {}

        self.user_handler.get_whitelist = mock_whitelist

    def test_get_users_returns_users(self):
        self.iamMock.list_users.return_value = {'Users': ['Klaus']}

        users = self.user_handler.get_users()

        self.boto3Mock.client.assert_called_once_with('iam')
        self.assertEqual(users, ['Klaus'])

    def test_fetch_unwanted_resources_returns_empty_generator_if_users_are_empty(self):
        self.iamMock.list_users.return_value = {'Users': []}
        unwanted_users = self.user_handler.fetch_unwanted_resources()
        self.assertEqual(len(list(unwanted_users)), 0)

    def test_fetch_unwanted_resources_returns_resource_wrapper_if_users_are_not_emtpy(self):
        iam_user = 'iam.User'
        expected_unwanted_user = Resource(resource=self.user,
                                          resource_type=iam_user,
                                          resource_id=self.user['Arn'],
                                          creation_date=self.user['CreateDate'],
                                          region='global')

        unwanted_users = self.user_handler.fetch_unwanted_resources()

        self.assertEqual(list(unwanted_users)[0], expected_unwanted_user)
        self.assertEqual(len(list(unwanted_users)), 0)

    def test_unwanted_resources_does_omit_ignore_list(self):
        self.user_handler.ignored_resources = [self.user_arn]
        unwanted_users = self.user_handler.fetch_unwanted_resources()

        self.assertEqual(len(list(unwanted_users)), 0)

    def test_whitelist_is_ignored_if_empty(self):
        unwanted_users = self.user_handler.fetch_unwanted_resources()
        self.assertEqual(len(list(unwanted_users)), 1)

    def test_unwanted_resources_does_omit_whitelist(self):
        def mock_whitelist():
                return {'Arns': [{'Arn': self.user_arn, 'Reason':'any reason'}]}
        self.user_handler.get_whitelist = mock_whitelist

        unwanted_users = self.user_handler.fetch_unwanted_resources()

        self.assertEqual(len(list(unwanted_users)), 0)

class AwsIamPolicyHandlerTest(unittest2.TestCase):

    def setUp(self):
        def mock_region_filter(ignore):
            return True
        self.boto3Mock = patch("monocyte.handler.iam.boto3").start()
        self.iamClientMock = MagicMock()
        self.boto3Mock.client.return_value = self.iamClientMock
        self.iamResourceMock = MagicMock()
        self.boto3Mock.resource.return_value = self.iamResourceMock
        self.policy_handler = IamPolicy(mock_region_filter)
        def mock_whitelist():
            return {}

        self.policy_handler.get_whitelist = mock_whitelist

    def test_get_policies_return_policies(self):
        self.iamClientMock.list_policies.return_value = {'IsTruncated': False, 'Policies': [{'Arn': 'arn:aws:iam:123456789'}]}
        policies = self.policy_handler.get_policies()
        self.boto3Mock.client.assert_called_once_with('iam')
        self.assertEqual(policies, [{'Arn': 'arn:aws:iam:123456789'}])

    def test_get_policy_document_return_document(self):
        policyVersionMock = MagicMock(document = {'Statement':[{'Action': ['s3:test3', 's4:test4']}]})
        self.iamResourceMock.PolicyVersion.return_value = policyVersionMock
        document = self.policy_handler.get_policy_document('arn', 'version')
        self.boto3Mock.resource.assert_called_once_with('iam')
        self.assertEqual(document, {'Statement':[{'Action': ['s3:test3', 's4:test4']}]})

