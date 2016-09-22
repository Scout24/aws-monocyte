from __future__ import print_function, absolute_import, division

import os
import unittest2
from monocyte.handler.iam import AwsIamPlugin
from moto import mock_iam

os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['no_proxy'] = ''


class AwsIamPluginTest(unittest2.TestCase):
    def setUp(self):
        self.dry_run = True
        self.aws_iam_plugin = AwsIamPlugin(self.dry_run)

    @mock_iam
    def test_check_users_user_found(self):
        test_user = [{'UserName': 'test1', 'Path': '/',
                      'UserId': 'QWERTZU', 'Arn': 'arn:aws:iam::123456789:user/test1'}]
        self.assertFalse(self.aws_iam_plugin.check_users(test_user))

    @mock_iam
    def test_check_users_users_found(self):
        test_user = [{'UserName': 'test1', 'Path': '/',
                      'UserId': 'QWERTZU', 'Arn': 'arn:aws:iam::123456789:user/test1'},
                     {'UserName': 'test2', 'Path': '/',
                      'UserId': 'ASDFGHJ', 'Arn': 'arn:aws:iam::123456789:user/test1'}]
        self.assertFalse(self.aws_iam_plugin.check_users(test_user))

    @mock_iam
    def test_check_users_no_user_found(self):
        test_user = []
        self.assertTrue(self.aws_iam_plugin.check_users(test_user))
