from __future__ import print_function, absolute_import, division
from unittest2 import TestCase
from mock import Mock

from monocyte.plugins.status_mail_plugin import StatusMailPlugin
from monocyte.handler import Resource


class StatusMailPluginTest(TestCase):
    def setUp(self):
        self.test_recipients = ["test_de@test.de", "test_com@test.com"]
        self.test_resources = [Resource(42, "ec2 instance", "12345", "date1", "us"),
                               Resource(42, "ec2 volume", "3312345", "date2", "us")]
        self.test_region = "eu-west-1"
        self.test_sender = "sender@test.com"
        self.test_account_name = "IS24-Pro-Test"
        self.test_status_mail_plugin = StatusMailPlugin(self.test_resources,
                                                        self.test_region,
                                                        self.test_sender,
                                                        self.test_account_name,
                                                        recipients=self.test_recipients)

    def test_of_email_body_in_case_of_action(self):
        body = self.test_status_mail_plugin.body
        expected_body = '''Dear AWS User,

our Compliance checker found some AWS resources outside of Europe in your account.
Please check and delete the following resources:

Account: IS24-Pro-Test
Region: us
\tec2 volume instance with identifier 3312345, created date2
\tec2 instance instance with identifier 12345, created date1

 Kind regards.
\tYour Compliance Team'''
        self.maxDiff = None
        self.assertEqual(body, expected_body)

    def test_email_sending_only_if_resources_are_given(self):
        self.test_status_mail_plugin.resources = []
        self.test_status_mail_plugin.send_email = Mock()

        self.test_status_mail_plugin.run()

        self.assertEqual(self.test_status_mail_plugin.send_email.call_count, 0)
