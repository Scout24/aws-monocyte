from __future__ import print_function, absolute_import, division

import os
import unittest2
from monocyte.handler import Resource
from mock import patch, MagicMock
from monocyte.handler.iam import User, InlinePolicy
from monocyte.handler.iam import IamPolicy, Policy

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
            return {'Arns': [{'Arn': self.user_arn, 'Reason': 'any reason'}]}

        self.user_handler.get_whitelist = mock_whitelist

        unwanted_users = self.user_handler.fetch_unwanted_resources()

        self.assertEqual(len(list(unwanted_users)), 0)

class AwsPolicyHandler(unittest2.TestCase):
    def setUp(self):
        self.policy_handler = Policy(MagicMock)

    def test_check_policy_resource_forbidden_returns_false_for_wildcard_in_resource_string(self):
        actions = ['*:*', 's23:333']
        resource = 'aws::s3:*'
        self.assertFalse(self.policy_handler.check_policy_resource_for_forbidden_string(actions, resource))

    def test_check_policy_resource_forbidden_returns_true_for_only_wildcard_in_resource_string(self):
        actions = ['*:*', 's23:333']
        resource = '*'
        self.assertTrue(self.policy_handler.check_policy_resource_for_forbidden_string(actions, resource))

    def test_check_policy_resource_forbidden_returns_false_for_only_wildcard_in_resource_string_but_elb(self):
        actions = ['elsaticloadbalanacing:*', 's23:333']
        resource = '*'
        self.assertTrue(self.policy_handler.check_policy_resource_for_forbidden_string(actions, resource))

    def test_check_policy_resource_forbidden_returns_false_for_only_wildcard_in_resource_string_but_elb(self):
        actions = ['s3:*', 's23:333']
        resource = ['*']
        self.assertTrue(self.policy_handler.check_policy_resource_for_forbidden_string(actions, resource))

    def test_get_policy_resource_get_statement_no_list(self):
        policy_document = {'Statement': {'Action': 'logs:CreateLogGroup',
                                          'Effect': 'Allow',
                                          'Resource': 'arn:aws:logs::*'}}
        expected_resource = 'arn:aws:logs::*'
        self.assertEqual(expected_resource, self.policy_handler.get_policy_resource(policy_document))

    def test_get_policy_resource_get_statement_list(self):
        policy_document = {'Statement': [{'Action': 'logs:CreateLogGroup',
                                         'Effect': 'Allow',
                                         'Resource': 'arn:aws:logs::*'}]}
        expected_resource = 'arn:aws:logs::*'
        self.assertEqual(expected_resource, self.policy_handler.get_policy_resource(policy_document))

    def test_check_policy_resource_forbidden_returns_false_for_no_wildcard_in_resource(self):
        actions = ['*:*', 's23:333']
        resource = 'aws::s3:dsdf'
        self.assertFalse(self.policy_handler.check_policy_resource_for_forbidden_string(actions, resource))


    def test_check_action_for_forbidden_string_returns_false_for_no_wildcard(self):
        actions = ['is3:s3', 's23:333']
        self.assertFalse(self.policy_handler.check_policy_action_for_forbidden_string(actions))

    def test_check_action_for_forbidden_string_returns_true_for_one_wildcard(self):
        actions = ['*', 's23:333']
        self.assertTrue(self.policy_handler.check_policy_action_for_forbidden_string(actions))

    def test_check_action_for_forbidden_string_returns_true_for_two_wildcard(self):
        actions = ['*:*', 's23:333']
        self.assertTrue(self.policy_handler.check_policy_action_for_forbidden_string(actions))

    def test_gather_actions_returns_list_for_action_list(self):
        policy_document = {'Statement': [{'Action': ['logs:CreateLogGroup', 'logs:foobar'],
                                            'Effect': 'Allow',
                                            'Resource': 'arn:aws:logs::*'}]}
        expected_list = ['logs:CreateLogGroup', 'logs:foobar']
        self.assertEqual(expected_list, self.policy_handler.gather_actions(policy_document))

    def test_gather_actions_returns_list_for_action_string(self):
        policy_document = {'Statement': [{'Action': 'logs:CreateLogGroup',
                                          'Effect': 'Allow',
                                          'Resource': 'arn:aws:logs::*'}]}
        expected_list = ['logs:CreateLogGroup']
        self.assertEqual(expected_list, self.policy_handler.gather_actions(policy_document))

    def test_gather_actions_returns_list_for_multiple_action_string(self):
        policy_document = {'Statement': [{'Action': 'logs:CreateLogGroup',
                                          'Effect': 'Allow',
                                          'Resource': 'arn:aws:logs::*'},
                                         {'Action': 'logs2:CreateLogGroup',
                                          'Effect': 'Allow',
                                          'Resource': 'arn:aws:logs::*'}]}
        expected_list = ['logs:CreateLogGroup', 'logs2:CreateLogGroup']
        self.assertEqual(expected_list, self.policy_handler.gather_actions(policy_document))

    def test_gather_actions_returns_list_for_statement_no_list_but_action(self):
        policy_document = {'Statement': {'Action':['logs:CreateLogGroup', 'ec2:Attache'],
                                          'Effect': 'Allow',
                                          'Resource': 'arn:aws:logs::*'}}
        expected_list = ['logs:CreateLogGroup', 'ec2:Attache']
        self.assertEqual(expected_list, self.policy_handler.gather_actions(policy_document))

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
        self.iamClientMock.list_policies.return_value = {'IsTruncated': False,
                                                         'Policies': [{'Arn': 'arn:aws:iam:123456789'}]}
        policies = self.policy_handler.get_policies()
        self.boto3Mock.client.assert_called_once_with('iam')
        self.assertEqual(policies, [{'Arn': 'arn:aws:iam:123456789'}])

    def test_get_policy_document_return_document(self):
        policyVersionMock = MagicMock(document={'Statement': [{'Action': ['s3:test3', 's4:test4']}]})
        self.iamResourceMock.PolicyVersion.return_value = policyVersionMock
        document = self.policy_handler.get_policy_document('arn', 'version')
        self.boto3Mock.resource.assert_called_once_with('iam')
        self.assertEqual(document, {'Statement': [{'Action': ['s3:test3', 's4:test4']}]})

    def test_fetch_unwanted_resources_returns_empty_if_no_policies(self):
        policyVersionMock = MagicMock(document={})
        self.iamResourceMock.PolicyVersion.return_value = policyVersionMock
        self.iamClientMock.list_policies.return_value = {'IsTruncated': False, 'Policies': []}
        self.assertEqual(len(list(self.policy_handler.fetch_unwanted_resources())), 0)

    def test_fetch_unwanted_resources_returns_true_if_forbidden_action(self):
        iam_policy = 'iam.IamPolicy'
        policyVersionMock = MagicMock(document={'Statement': [{'Action': ['s3:test3', '*:*'],'Resource': 'aws:s2222'}]})
        self.iamResourceMock.PolicyVersion.return_value = policyVersionMock
        policy = {'IsTruncated': False,
                  'Policies': [{'Arn': 'arn:aws:iam:123456789', 'DefaultVersionId': 'v1', 'CreateDate': '2012-06-12'}]}
        expected_unwanted_user = Resource(resource=policy['Policies'][0],
                                          resource_type=iam_policy,
                                          resource_id=policy['Policies'][0]['Arn'],
                                          creation_date=policy['Policies'][0]['CreateDate'],
                                          region='global')

        self.iamClientMock.list_policies.return_value = policy
        unwanted_resource = self.policy_handler.fetch_unwanted_resources()
        self.assertEqual(list(unwanted_resource)[0], expected_unwanted_user)

    def test_fetch_unwanted_resources_returns_false_if_no_forbidden_action(self):
        policyVersionMock = MagicMock(document={'Statement': [{'Action': ['s3:test3', 's*:s*'], 'Resource': 'aws:s2222'}]})
        self.iamResourceMock.PolicyVersion.return_value = policyVersionMock
        policy = {'IsTruncated': False,
                  'Policies': [{'Arn': 'arn:aws:iam:123456789', 'DefaultVersionId': 'v1', 'CreateDate': '2012-06-12'}]}

        self.iamClientMock.list_policies.return_value = policy
        unwanted_resource = self.policy_handler.fetch_unwanted_resources()
        self.assertEqual(len(list(unwanted_resource)),0)



class AwsInlinePolicyHandlerTest(unittest2.TestCase):
    def setUp(self):
        def mock_region_filter(ignore):
            return True

        self.boto3Mock = patch("monocyte.handler.iam.boto3").start()
        self.iamClientMock = MagicMock()
        self.boto3Mock.client.return_value = self.iamClientMock
        self.iamResourceMock = MagicMock()
        self.boto3Mock.resource.return_value = self.iamResourceMock
        self.policy_handler = InlinePolicy(mock_region_filter)

        def mock_whitelist():
            return {}

        self.policy_handler.get_whitelist = mock_whitelist

    def test_get_iam_role_name_return_role_name(self):
        self.iamClientMock.list_roles.return_value = {'Roles': [{'Arn': 'arn:aws:iam::123456789101:role/foo-bar-file',
                                                                 'AssumeRolePolicyDocument': {
                                                                     'Statement': [{'Action': 'sts:AssumeRole',
                                                                                     'Effect': 'Allow',
                                                                                     'Principal': {
                                                                                         'AWS': 'arn:aws:iam::9876543210:root'},
                                                                                     'Sid': ''}],
                                                                     'Version': '2012-10-17'},
                                                                 'CreateDate': '01.01.1989',
                                                                 'Path': '/',
                                                                 'RoleId': 'FOOAJ4DHXC5V55TMCIBAR',
                                                                 'RoleName': 'foo-bar-file'}]}
        role = self.policy_handler.get_all_iam_roles_in_account()
        self.assertEqual(role[0]['RoleName'], 'foo-bar-file')

    def test_get_iam_role_names_return_role_names(self):
        self.iamClientMock.list_roles.return_value = {'Roles': [{'Arn': 'arn:aws:iam::123456789101:role/foo-bar-file',
                                                                 'AssumeRolePolicyDocument': {
                                                                     'Statement': [{'Action': 'sts:AssumeRole',
                                                                                     'Effect': 'Allow',
                                                                                     'Principal': {
                                                                                         'AWS': 'arn:aws:iam::9876543210:root'},
                                                                                     'Sid': ''}],
                                                                     'Version': '2012-10-17'},
                                                                 'CreateDate': '01.01.1989',
                                                                 'Path': '/',
                                                                 'RoleId': 'FOOAJ4DHXC5V55TMCIBAR',
                                                                 'RoleName': 'foo-bar-file'},
                                                                {'Arn': 'arn:aws:iam::66666666666:role/foo-foo-foo',
                                                                 'AssumeRolePolicyDocument': {
                                                                     'Statement': [{'Action': 'sts:AssumeRole',
                                                                                     'Effect': 'Allow',
                                                                                     'Principal': {
                                                                                         'Service': 'lambda.amazonaws.com'}}],
                                                                     'Version': '2012-10-17'},
                                                                 'CreateDate': '01.01.1970',
                                                                 'Path': '/',
                                                                 'RoleId': 'HSKASODO2S80SDDAD',
                                                                 'RoleName': 'foo-foo-key'}]}
        role_names = self.policy_handler.get_all_iam_roles_in_account()
        roles = []
        for role in role_names:
            roles.append(role['RoleName'])
        self.assertEqual(roles, ['foo-bar-file', 'foo-foo-key'])

    def test_get_all_inline_policies_for_role_returns_empty_list_for_no_inline_policies(self):
        role_name = ''
        role_object = MagicMock()
        role_policy_object = MagicMock()
        self.iamResourceMock.Role.return_value = role_object
        role_object.policies.all.return_value = role_policy_object

        role_policies = self.policy_handler.get_all_inline_policies_for_role(role_name)
        role_object.policies.all.assert_called_once()
        self.iamResourceMock.Role.assert_called_once()
        role_policy_object.assert_not_called()

        self.assertEqual(role_policies, [])

    def test_get_all_inline_policies_for_role_returns_inline_policy(self):
        role_name = 'foo-bar-file'
        role_mock = MagicMock()
        self.iamResourceMock.Role.return_value = role_mock
        role_mock.policies.all.return_value = [42]

        role_policies = self.policy_handler.get_all_inline_policies_for_role(role_name)
        self.assertEqual(role_policies, [42])

    def test_check_inline_policy_action_for_forbidden_string_returns_false_if_string_not_found(self):
        policy_document = "S3:foo"
        return_value = self.policy_handler.check_policy_action_for_forbidden_string(policy_document)
        self.assertFalse(return_value)

    def test_check_inline_policy_action_for_forbidden_string_returns_false_if_policiy_list_not_found(self):
        policy_document = ['S3:foo', 's3:bar']
        return_value = self.policy_handler.check_policy_action_for_forbidden_string(policy_document)
        self.assertFalse(return_value)

    def test_check_inline_policy_action_for_forbidden_string_returns_true_if_string_found(self):
        policy_document = "*:*"
        return_value = self.policy_handler.check_policy_action_for_forbidden_string(policy_document)
        self.assertTrue(return_value)

    def test_check_inline_policy_action_for_forbidden_string_returns_true_if_policy_list_found(self):
        policy_document = ['*:*', 's3:3']
        return_value = self.policy_handler.check_policy_action_for_forbidden_string(policy_document)
        self.assertTrue(return_value)

    def test_fetch_unwanted_resources_returns_empty_if_no_role_found(self):
        self.assertEqual(len(list(self.policy_handler.fetch_unwanted_resources())), 0)

    def test_fetch_unwanted_resources_return_false_if_elb_in_action(self):
        role_mock = MagicMock(arn='arn:aws:iam::123456789101:role/foo-bar-file',create_date='01.01.1989', role_name='foo-bar-file')
        list_role_mock = {'Roles': [role_mock]}
        self.iamClientMock.list_roles.return_value = list_role_mock

        policy_mock = MagicMock(policy_document={'Statement': [{'Action': ['elasticloadbalancing:test3', 's3:test1'], 'Resource': ['arn:aws:s3:::test3']}]})
        role_mock.policies.all.return_value = [policy_mock]

        self.iamResourceMock.Role.return_value = role_mock

        unwanted_resource = self.policy_handler.fetch_unwanted_resources()
        self.assertEqual(len(list(unwanted_resource)), 0)

    def test_fetch_unwanted_resources_return_false_if_action_string_not_found(self):
        role_mock = MagicMock(arn='arn:aws:iam::123456789101:role/foo-bar-file',create_date='01.01.1989', role_name='foo-bar-file')
        list_role_mock = {'Roles': [role_mock]}
        self.iamClientMock.list_roles.return_value = list_role_mock

        policy_mock = MagicMock(policy_document={'Statement': [{'Action': ['s4:test3', 's*:s*'], 'Resource': ['arn:aws:s3:::test3']}]})
        role_mock.policies.all.return_value = [policy_mock]

        self.iamResourceMock.Role.return_value = role_mock

        unwanted_resource = self.policy_handler.fetch_unwanted_resources()
        self.assertEqual(len(list(unwanted_resource)), 0)

    def test_fetch_unwanted_resources_return_true_if_action_string_found(self):
        inline_policy = 'iam.InlinePolicy'
        role_mock = MagicMock()
        sample_role = {'Arn': 'arn:aws:iam::123456789101:role/foo-bar-file',
                       'AssumeRolePolicyDocument': {
                           'Statement': [{'Action': 'sts:AssumeRole',
                                          'Effect': 'Allow',
                                          'Principal': {
                                              'AWS': 'arn:aws:iam::9876543210:root'},
                                          'Sid': ''}],
                           'Version': '2012-10-17'},
                       'CreateDate': '01.01.1989',
                       'Path': '/',
                       'RoleId': 'FOOAJ4DHXC5V55TMCIBAR',
                       'RoleName': 'foo-bar-file'}
        list_role_mock = {'Roles': [sample_role]}
        self.iamClientMock.list_roles.return_value = list_role_mock

        policy_mock = MagicMock(policy_document={'Statement': [{'Action': ['s4:test3', '*:*'], 'Resource': ['arn:aws:s3:::test3']}]})
        role_mock.policies.all.return_value = [policy_mock]

        self.iamResourceMock.Role.return_value = role_mock
        expected_unwanted_role = Resource(resource=sample_role,
                                          resource_type=inline_policy,
                                          resource_id=sample_role['Arn'],
                                          creation_date=sample_role['CreateDate'],
                                          region='global')

        unwanted_resource = self.policy_handler.fetch_unwanted_resources()
        unwanted_resource_list = list(unwanted_resource)
        self.assertEqual(len(list(unwanted_resource_list)), 1)
        self.assertEqual(expected_unwanted_role, unwanted_resource_list[0])

    def test_fetch_unwanted_resources_return_true_if_action_and_resource_string_found(self):
        inline_policy = 'iam.InlinePolicy'
        role_mock = MagicMock()
        sample_role = {'Arn': 'arn:aws:iam::123456789101:role/foo-bar-file',
                       'AssumeRolePolicyDocument': {
                           'Statement': [{'Action': 'sts:AssumeRole',
                                          'Effect': 'Allow',
                                          'Principal': {
                                              'AWS': 'arn:aws:iam::9876543210:root'},
                                          'Sid': ''}],
                           'Version': '2012-10-17'},
                       'CreateDate': '01.01.1989',
                       'Path': '/',
                       'RoleId': 'FOOAJ4DHXC5V55TMCIBAR',
                       'RoleName': 'foo-bar-file'}
        list_role_mock = {'Roles': [sample_role]}
        self.iamClientMock.list_roles.return_value = list_role_mock

        policy_mock = MagicMock(policy_document={'Statement': [{'Action': ['elasticloadbalancing:test3', '*:*'], 'Resource': ['arn:aws:s3:::test3']}]})
        role_mock.policies.all.return_value = [policy_mock]

        self.iamResourceMock.Role.return_value = role_mock
        expected_unwanted_role = Resource(resource=sample_role,
                                          resource_type=inline_policy,
                                          resource_id=sample_role['Arn'],
                                          creation_date=sample_role['CreateDate'],
                                          region='global')

        unwanted_resource = self.policy_handler.fetch_unwanted_resources()
        unwanted_resource_list = list(unwanted_resource)
        self.assertEqual(len(list(unwanted_resource_list)), 1)
        self.assertEqual(expected_unwanted_role, unwanted_resource_list[0])
