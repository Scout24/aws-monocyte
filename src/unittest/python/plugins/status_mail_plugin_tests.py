from __future__ import print_function, absolute_import, division

import boto3
import os
from mock import Mock, patch
from monocyte.handler import Resource
from monocyte.plugins.status_mail_plugin import StatusMailPlugin, UsofaStatusMailPlugin
from moto import mock_ses, mock_s3
from unittest2 import TestCase

EXPECTED_PART_HEADER = """Dear AWS User,

our Compliance checker found some issues in your account.
"""
EXPECTED_PART_DRY_RUN = "Please check the following resources:\n"
EXPECTED_PART_NO_DRY_RUN = "Please check the following deleted resources:\n"
EXPECTED_PART_UNWANTED_FILLED = """
Account: test-account
Region: us
\tec2 instance with identifier 12345, created date1.
\tec2 volume with identifier 3312345, created date2.
"""
EXPECTED_PART_UNWANTED_EMPTY = """
Account: test-account
\tNone
"""
EXPECTED_PART_UNWANTED_FILLED_WITH_REASON = """
Account: test-account
Region: us
\tec2 instance with identifier 12345, created date1. Please follow the principal of least privilege and do not use Action : *
\tec2 volume with identifier 3312345, created date2.
"""

EXPECTED_PART_PROBLEMATIC_FILLED = """
Additionally we had issues checking the following resource, please ensure that they are in the proper region:
Region: us
\tec2 instance with identifier 67890, created date1.
\tec2 volume with identifier 1112345, created date2.
"""

EXPECTED_PART_PROBLEMATIC_EMPTY = ""
EXPECTED_PART_FOOTER = """
 Kind regards.
\tYour Compliance Team"""

os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['no_proxy'] = ''


class StatusMailPluginTest(TestCase):
    def setUp(self):
        self.test_recipients = ["test_de@test.invalid", "test_com@test.invalid"]
        self.unwanted_resources = [
            Resource(42, "ec2 instance", "12345", "date1", "us"),
            Resource(42, "ec2 volume", "3312345", "date2", "us")]
        self.problematic_resources = [
            Resource(23, "ec2 instance", "67890", "date1", "us"),
            Resource(23, "ec2 volume", "1112345", "date2", "us")]
        self.dry_run = True
        self.reason = 'Do not do it'
        self.test_region = "eu-west-1"
        self.test_sender = "sender@test.invalid"
        self.test_status_mail_plugin = StatusMailPlugin(self.unwanted_resources,
                                                        self.problematic_resources,
                                                        self.dry_run,
                                                        region=self.test_region,
                                                        sender=self.test_sender,
                                                        recipients=self.test_recipients)

    # Moto's mock_iam does not support the get_account_alias() function.
    @patch('monocyte.plugins.status_mail_plugin.StatusMailPlugin._get_account_alias')
    def test_of_email_body_in_case_of_action(self, mock_get_account_alias):
        mock_get_account_alias.return_value = "test-account"
        body = self.test_status_mail_plugin.body
        expected_body = (EXPECTED_PART_HEADER +
                         EXPECTED_PART_DRY_RUN +
                         EXPECTED_PART_UNWANTED_FILLED +
                         EXPECTED_PART_PROBLEMATIC_FILLED +
                         EXPECTED_PART_FOOTER)

        self.maxDiff = None
        self.assertEqual(body, expected_body)

    @patch('monocyte.plugins.status_mail_plugin.StatusMailPlugin._get_account_alias')
    def test_of_email_body_problematic_resources_with_reason(self, mock_get_account_alias):
        mock_get_account_alias.return_value = "test-account"
        unwanted_resources = [
            Resource(42, "ec2 instance", "12345", "date1", "us", reason='Please follow the principal of least privilege and do not use Action : *'),
            Resource(42, "ec2 volume", "3312345", "date2", "us")]
        problematic_resources = []
        dry_run = False
        test_status_mail_plugin = StatusMailPlugin(unwanted_resources,
                                                   problematic_resources,
                                                   dry_run,
                                                   region=self.test_region,
                                                   sender=self.test_sender,
                                                   recipients=self.test_recipients)
        body = test_status_mail_plugin.body
        expected_body = (EXPECTED_PART_HEADER +
                         EXPECTED_PART_NO_DRY_RUN +
                         EXPECTED_PART_UNWANTED_FILLED_WITH_REASON +
                         EXPECTED_PART_FOOTER)
        self.maxDiff = None
        self.assertEqual(body, expected_body)

    @patch('monocyte.plugins.status_mail_plugin.StatusMailPlugin._get_account_alias')
    def test_of_email_body_no_problematic_resources(self, mock_get_account_alias):
        mock_get_account_alias.return_value = "test-account"
        test_status_mail_plugin = StatusMailPlugin(self.unwanted_resources,
                                                   [],
                                                   self.dry_run,
                                                   region=self.test_region,
                                                   sender=self.test_sender,
                                                   recipients=self.test_recipients)
        body = test_status_mail_plugin.body
        expected_body = (EXPECTED_PART_HEADER +
                         EXPECTED_PART_DRY_RUN +
                         EXPECTED_PART_UNWANTED_FILLED +
                         EXPECTED_PART_PROBLEMATIC_EMPTY +
                         EXPECTED_PART_FOOTER)

        self.maxDiff = None
        self.assertEqual(body, expected_body)

    @patch('monocyte.plugins.status_mail_plugin.StatusMailPlugin._get_account_alias')
    def test_of_email_body_no_unwanted_resources(self, mock_get_account_alias):
        mock_get_account_alias.return_value = "test-account"
        test_status_mail_plugin = StatusMailPlugin([],
                                                   self.problematic_resources,
                                                   self.dry_run,
                                                   region=self.test_region,
                                                   sender=self.test_sender,
                                                   recipients=self.test_recipients)
        body = test_status_mail_plugin.body
        expected_body = (EXPECTED_PART_HEADER +
                         EXPECTED_PART_DRY_RUN +
                         EXPECTED_PART_UNWANTED_EMPTY +
                         EXPECTED_PART_PROBLEMATIC_FILLED +
                         EXPECTED_PART_FOOTER)

        self.maxDiff = None
        self.assertEqual(body, expected_body)

    @patch('monocyte.plugins.status_mail_plugin.StatusMailPlugin._get_account_alias')
    def test_of_email_body_no_dry_run(self, mock_get_account_alias):
        mock_get_account_alias.return_value = "test-account"
        test_status_mail_plugin = StatusMailPlugin(self.unwanted_resources,
                                                   self.problematic_resources,
                                                   False,
                                                   region=self.test_region,
                                                   sender=self.test_sender,
                                                   recipients=self.test_recipients)
        body = test_status_mail_plugin.body
        expected_body = (EXPECTED_PART_HEADER +
                         EXPECTED_PART_NO_DRY_RUN +
                         EXPECTED_PART_UNWANTED_FILLED +
                         EXPECTED_PART_PROBLEMATIC_FILLED +
                         EXPECTED_PART_FOOTER)

        self.maxDiff = None
        self.assertEqual(body, expected_body)

    def test_email_sending_only_if_resources_are_given(self):
        self.test_status_mail_plugin.unwanted_resources = []
        self.test_status_mail_plugin.problematic_resources = []
        self.test_status_mail_plugin.send_email = Mock()

        self.test_status_mail_plugin.run()

        self.assertEqual(self.test_status_mail_plugin.send_email.call_count, 0)

    @mock_ses
    @patch('monocyte.plugins.status_mail_plugin.StatusMailPlugin._get_account_alias')
    def test_send_mail_ok(self, mock_get_account_alias):
        mock_get_account_alias.return_value = "test-account"

        conn = boto3.client('ses', region_name=self.test_region)
        conn.verify_email_identity(EmailAddress=self.test_sender)

        self.test_status_mail_plugin.run()

        send_quota = conn.get_send_quota()
        sent_count = int(send_quota['SentLast24Hours'])
        self.assertEqual(sent_count, 1)

    @mock_ses
    @patch('monocyte.plugins.status_mail_plugin.StatusMailPlugin._get_account_alias')
    def test_body_property_set_failure(self, mock_get_account_alias):
        mock_get_account_alias.return_value = "test-account"
        not_expected_body = 'CHANGED BODY'
        test_status_mail_plugin = StatusMailPlugin(self.unwanted_resources,
                                                   self.problematic_resources,
                                                   self.dry_run,
                                                   region=self.test_region,
                                                   sender=self.test_sender,
                                                   recipients=self.test_recipients,
                                                   body=not_expected_body)

        expected_body = (EXPECTED_PART_HEADER +
                         EXPECTED_PART_DRY_RUN +
                         EXPECTED_PART_UNWANTED_FILLED +
                         EXPECTED_PART_PROBLEMATIC_FILLED +
                         EXPECTED_PART_FOOTER)
        self.assertNotEqual(test_status_mail_plugin.body, not_expected_body)
        self.assertEqual(test_status_mail_plugin.body, expected_body)


class UsofaStatusMailPluginTest(TestCase):
    def setUp(self):
        self.test_recipients = ["test_de@test.invalid", "test_com@test.invalid"]
        self.unwanted_resources = [
            Resource(42, "ec2 instance", "12345", "date1", "us"),
            Resource(42, "ec2 volume", "3312345", "date2", "us")]
        self.problematic_resources = [
            Resource(23, "ec2 instance", "67890", "date1", "us"),
            Resource(23, "ec2 volume", "1112345", "date2", "us")]
        self.dry_run = True
        self.test_region = "eu-west-1"
        self.test_sender = "sender@test.invalid"
        self.usofa_bucket_name = "usofbucket"
        self.test_status_mail_plugin = UsofaStatusMailPlugin(
                self.unwanted_resources,
                self.problematic_resources,
                self.dry_run,
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
                self.unwanted_resources,
                self.problematic_resources,
                self.dry_run,
                region=self.test_region,
                sender=self.test_sender,
                usofa_bucket_name=self.usofa_bucket_name)
        recipients = self.test_status_mail_plugin.recipients
        expected_recipients = ['foo@test.invalid']
        self.assertEqual(recipients, expected_recipients)

    @mock_s3
    def test_get_usofa_data__ok(self):
        conn = boto3.client('s3', region_name=self.test_region)
        conn.create_bucket(Bucket=self.usofa_bucket_name)
        conn.put_object(Bucket=self.usofa_bucket_name, Key="accounts.json", Body='"This is a test of USofA"')

        usofa_data = self.test_status_mail_plugin._get_usofa_data()
        self.assertEqual(usofa_data, "This is a test of USofA")
