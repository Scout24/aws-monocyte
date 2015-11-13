from __future__ import print_function, absolute_import, division
from unittest2 import TestCase
from mock import Mock, patch
from moto import mock_ses, mock_s3
import boto
from monocyte.plugins.status_mail_plugin import StatusMailPlugin, UsofaStatusMailPlugin
from monocyte.handler import Resource

EXPECTED_BODY = '''Dear AWS User,

our Compliance checker found some AWS resources outside of Europe in your account.
Please check and delete the following resources:

Account: test-account
Region: us
\tec2 instance instance with identifier 12345, created date1
\tec2 volume instance with identifier 3312345, created date2

 Kind regards.
\tYour Compliance Team'''


class StatusMailPluginTest(TestCase):
    def setUp(self):
        self.test_recipients = ["test_de@test.invalid", "test_com@test.invalid"]
        self.test_resources = [
            Resource(42, "ec2 instance", "12345", "date1", "us"),
            Resource(42, "ec2 volume", "3312345", "date2", "us")]
        self.test_region = "eu-west-1"
        self.test_sender = "sender@test.invalid"
        self.expected_body = EXPECTED_BODY
        self.test_status_mail_plugin = StatusMailPlugin(self.test_resources,
                                                        region=self.test_region,
                                                        sender=self.test_sender,
                                                        recipients=self.test_recipients)

    # Moto's mock_iam does not support the get_account_alias() function.
    @patch('monocyte.plugins.status_mail_plugin.StatusMailPlugin._get_account_alias')
    def test_of_email_body_in_case_of_action(self, mock_get_account_alias):
        mock_get_account_alias.return_value = "test-account"
        body = self.test_status_mail_plugin.body

        self.maxDiff = None
        self.assertEqual(body, self.expected_body)

    def test_email_sending_only_if_resources_are_given(self):
        self.test_status_mail_plugin.resources = []
        self.test_status_mail_plugin.send_email = Mock()

        self.test_status_mail_plugin.run()

        self.assertEqual(self.test_status_mail_plugin.send_email.call_count, 0)

    @mock_ses
    @patch('monocyte.plugins.status_mail_plugin.StatusMailPlugin._get_account_alias')
    def test_send_mail_ok(self, mock_get_account_alias):
        mock_get_account_alias.return_value = "test-account"

        conn = boto.connect_ses('the_key', 'the_secret')
        conn.verify_email_identity(self.test_sender)

        self.test_status_mail_plugin.run()

        send_quota = conn.get_send_quota()
        sent_count = int(
            send_quota['GetSendQuotaResponse']['GetSendQuotaResult'][
                'SentLast24Hours'])
        self.assertEqual(sent_count, 1)

    @mock_ses
    @patch('monocyte.plugins.status_mail_plugin.StatusMailPlugin._get_account_alias')
    def test_body_property_set_failure(self, mock_get_account_alias):
        mock_get_account_alias.return_value = "test-account"
        not_expected_body = 'CHANGED BODY'
        test_status_mail_plugin = StatusMailPlugin(self.test_resources,
                                                   region=self.test_region,
                                                   sender=self.test_sender,
                                                   recipients=self.test_recipients,
                                                   body=not_expected_body)

        self.assertNotEqual(test_status_mail_plugin.body, not_expected_body)
        self.assertEqual(test_status_mail_plugin.body, self.expected_body)


class UsofaStatusMailPluginTest(TestCase):
    def setUp(self):
        self.test_recipients = ["test_de@test.invalid", "test_com@test.invalid"]
        self.test_resources = [
            Resource(42, "ec2 instance", "12345", "date1", "us"),
            Resource(42, "ec2 volume", "3312345", "date2", "us")]
        self.test_region = "eu-west-1"
        self.test_sender = "sender@test.invalid"
        self.expected_body = EXPECTED_BODY
        self.usofa_bucket_name = "usofbucket"
        self.test_status_mail_plugin = UsofaStatusMailPlugin(
            self.test_resources,
            region=self.test_region,
            sender=self.test_sender,
            recipients=self.test_recipients,
            usofa_bucket_name=self.usofa_bucket_name)

    @patch('monocyte.plugins.status_mail_plugin.UsofaStatusMailPlugin._get_account_alias')
    @patch('monocyte.plugins.status_mail_plugin.UsofaStatusMailPlugin._get_usofa_data')
    def test_recipients_include_usofa_data(self, mock_get_usofa_data, mock_get_account_alias):
        mock_get_account_alias.return_value = "testaccount"
        mock_get_usofa_data.return_value = {
            'testaccount': {'id': '42', 'email': 'foo@test.invalid'},
            'otheraccount': {'id': '43', 'email': 'bar@test.invalid'}}

        recipients = self.test_status_mail_plugin.recipients
        expected_recipients = self.test_recipients
        expected_recipients.append('foo@test.invalid')
        self.assertEqual(recipients, expected_recipients)

    @patch('monocyte.plugins.status_mail_plugin.UsofaStatusMailPlugin._get_account_alias')
    @patch('monocyte.plugins.status_mail_plugin.UsofaStatusMailPlugin._get_usofa_data')
    def test_works_without_explicit_recipients(self, mock_get_usofa_data, mock_get_account_alias):
        mock_get_account_alias.return_value = "testaccount"
        mock_get_usofa_data.return_value = {
            'testaccount': {'id': '42', 'email': 'foo@test.invalid'},
            'otheraccount': {'id': '43', 'email': 'bar@test.invalid'}}

        # Do NOT pass a 'recipients' parameter!
        self.test_status_mail_plugin = UsofaStatusMailPlugin(
            self.test_resources,
            region=self.test_region,
            sender=self.test_sender,
            usofa_bucket_name=self.usofa_bucket_name)
        recipients = self.test_status_mail_plugin.recipients
        expected_recipients = ['foo@test.invalid']
        self.assertEqual(recipients, expected_recipients)

    @mock_s3
    def test_get_usofa_data__ok(self):
        conn = boto.s3.connect_to_region(self.test_region)
        conn.create_bucket(self.usofa_bucket_name)
        bucket = conn.get_bucket(self.usofa_bucket_name)
        key = boto.s3.key.Key(bucket)
        key.key = "accounts.json"
        key.set_contents_from_string('"This is a test of USofA"')

        usofa_data = self.test_status_mail_plugin._get_usofa_data()
        self.assertEqual(usofa_data, "This is a test of USofA")
