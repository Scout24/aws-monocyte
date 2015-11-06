from unittest import TestCase
from monocyte.plugins.ses_plugin import AwsSesPlugin
from moto import mock_ses


class AwsSesPluginTest(TestCase):

    def setUp(self):
        self.region = "eu-west-1"
        self.sender = "thomas.lehmann@immobilienscout24.de"
        self.subject = "AWS Monocyte"
        self.recipients = ["thomas.lehmann@immobilienscout24.de"]
        self.body = "myEmailBody"
        self.aws_ses_plugin = AwsSesPlugin(self.region, self.sender,
                                           self.subject, self.recipients, self.body)

    @mock_ses
    def test_send_mail_success(self):
        # self.aws_ses_plugin.send_email()
        pass