from __future__ import print_function, absolute_import, division
from unittest2 import TestCase
from mock import Mock
from moto import mock_ses
import boto
from monocyte.plugins.status_mail_plugin import StatusMailPlugin
from monocyte.handler import Resource


class StatusMailPluginTest(TestCase):
    def setUp(self):
        self.test_recipients = ["test_de@test.invalid", "test_com@test.invalid"]
        self.test_resources = [
            Resource(42, "ec2 instance", "12345", "date1", "us"),
            Resource(42, "ec2 volume", "3312345", "date2", "us")]
        self.test_region = "eu-west-1"
        self.test_sender = "sender@test.invalid"
        self.test_account_name = "test-account"
        self.expected_body = '''Dear AWS User,

our Compliance checker found some AWS resources outside of Europe in your account.
Please check and delete the following resources:

Account: test-account
Region: us
\tec2 instance instance with identifier 12345, created date1
\tec2 volume instance with identifier 3312345, created date2

 Kind regards.
\tYour Compliance Team'''
        self.test_status_mail_plugin = StatusMailPlugin(self.test_resources,
                                                        region=self.test_region,
                                                        sender=self.test_sender,
                                                        account_name=self.test_account_name,
                                                        recipients=self.test_recipients)

    def test_of_email_body_in_case_of_action(self):
        body = self.test_status_mail_plugin.body

        self.maxDiff = None
        self.assertEqual(body, self.expected_body)

    def test_email_sending_only_if_resources_are_given(self):
        self.test_status_mail_plugin.resources = []
        self.test_status_mail_plugin.send_email = Mock()

        self.test_status_mail_plugin.run()

        self.assertEqual(self.test_status_mail_plugin.send_email.call_count, 0)

    @mock_ses
    def test_send_mail_ok(self):
        conn = boto.connect_ses('the_key', 'the_secret')
        conn.verify_email_identity(self.test_sender)

        self.test_status_mail_plugin.send_email()

        send_quota = conn.get_send_quota()
        sent_count = int(
            send_quota['GetSendQuotaResponse']['GetSendQuotaResult'][
                'SentLast24Hours'])
        self.assertEqual(sent_count, 1)

    @mock_ses
    def test_body_property_set_failure(self):
        not_expected_body = 'CHANGED BODY'
        test_status_mail_plugin = StatusMailPlugin(self.test_resources,
                                                   region=self.test_region,
                                                   sender=self.test_sender,
                                                   account_name=self.test_account_name,
                                                   recipients=self.test_recipients,
                                                   body=not_expected_body)

        self.assertNotEqual(test_status_mail_plugin.body, not_expected_body)
        self.assertEqual(test_status_mail_plugin.body, self.expected_body)
