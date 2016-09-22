from __future__ import print_function, absolute_import, division

import os
import unittest2
from monocyte.handler import Resource
from mock import patch, Mock, MagicMock
from monocyte.handler.iam import User

os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['no_proxy'] = ''


class AwsIamHandlerTest(unittest2.TestCase):
    def setUp(self):
        self.user_handler = User([])
        self.boto3Mock = patch("monocyte.handler.iam.boto3").start()
        self.iamMock = MagicMock()
        self.iamMock.list_users.return_value = {'Users': []}
        self.boto3Mock.resource.return_value = self.iamMock

    def test_fetch_region_should_return_empty_array(self):
        self.assertEqual(self.user_handler.fetch_regions(), [])

    def test_get_users_users_returns_users(self):
        self.iamMock.list_users.return_value = {'Users': ['Klaus']}
        self.assertEqual(self.user_handler.get_users(), ['Klaus'])

    def test_fetch_unwanted_resources_returns_None_if_users_are_empty(self):
        self.assertEqual(self.user_handler.fetch_unwanted_resources(), None)

    def test_fetch_unwanted_resources_returns_resource_wrapper_if_users_are_not_emtpy(self):
        user = {
            'UserName': 'test1',
            'Arn': 'arn:aws:iam::123456789:user/test1',
            'CreateDate': '2016-11-29'
        }

        self.iamMock.list_users.return_value = {'Users': [user]}
        iam_user = 'iam User'
        expected_unwanted_user = Resource(resource=user,
                                          resource_type=iam_user,
                                          resource_id=user['Arn'],
                                          creation_date=user['CreateDate'])

        unwanted_users = self.user_handler.fetch_unwanted_resources()
        self.assertEqual(unwanted_users, [expected_unwanted_user])
