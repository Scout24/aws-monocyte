import unittest2
from mock import Mock, patch
from monocyte.handler import Handler


class HandlerTest(unittest2.TestCase):

    def setUp(self):
        self.identity_mock = Mock()
        self.identity_mock.get.return_value = 'any account id'
        self.sts_mock = Mock()
        self.sts_mock.get_caller_identity.return_value = self.identity_mock
        self.boto_mock = patch('monocyte.handler.boto3').start()
        self.boto_mock.client.return_value = self.sts_mock

        def mock_region_filter():
            return True
        self.handler = TestHandler(mock_region_filter)

    def test_get_account_id(self):

        account_id = self.handler.get_account_id()
        self.boto_mock.client.assert_called_once_with('sts')
        self.identity_mock.get.assert_called_once_with('Account')

        self.assertEqual('any account id', account_id)

    def test_get_whitelist_returns_whitelist_if_there_is_one_for_the_account(self):
        self.handler.whitelist = {'any account id': 'any whitelist'}

        self.assertEqual('any whitelist', self.handler.get_whitelist())

    def test_get_whitelist_returns_empty_whitelist_if_there_is_no_whitelist(self):
        self.handler.whitelist = {}

        self.assertEqual({}, self.handler.get_whitelist())


class TestHandler(Handler):
    def fetch_region_names(self):
        return []
