from __future__ import print_function, absolute_import, division

from unittest import TestCase
from moto import mock_ses
import boto

from monocyte.plugins.ses_plugin import AwsSesPlugin


class AwsSesPluginTest(TestCase):

    def setUp(self):
        self.resources = "42"
        self.region = "eu-west-1"
        self.sender = "thomas.lehmann@immobilienscout24.de"
        self.subject = "AWS Monocyte"
        self.recipients = ["thomas.lehmann@immobilienscout24.de"]
        self.body = "myEmailBody"
        self.aws_ses_plugin = AwsSesPlugin(self.resources, self.region, self.sender,
                                           self.subject, self.recipients, self.body)

    def test_ses_plugin_properties(self):
        self.assertEqual(self.aws_ses_plugin.sender, self.sender)
        self.assertEqual(self.aws_ses_plugin.recipients, self.recipients)
        self.assertEqual(self.aws_ses_plugin.body, self.body)

    @mock_ses
    def test_should_send_mail(self):
        conn = boto.connect_ses('the_key', 'the_secret')
        conn.verify_email_identity("thomas.lehmann@immobilienscout24.de")

        self.aws_ses_plugin.send_email()

        send_quota = conn.get_send_quota()
        sent_count = int(send_quota['GetSendQuotaResponse']['GetSendQuotaResult']['SentLast24Hours'])
        self.assertEqual(sent_count, 1)

