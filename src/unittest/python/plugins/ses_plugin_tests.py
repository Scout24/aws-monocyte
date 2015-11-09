from unittest import TestCase
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
