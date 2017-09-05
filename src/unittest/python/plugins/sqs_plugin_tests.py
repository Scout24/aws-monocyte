from __future__ import print_function, absolute_import, division
import json
import logging
import os
from unittest2 import TestCase
from moto import mock_sqs
import boto3
from mock import patch
from monocyte.plugins.sqs_plugin import AwsSQSPlugin

os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['no_proxy'] = ''


class AwsSQSPluginTest(TestCase):
    def setUp(self):
        self.queue_region = "eu-west-1"
        self.queue_account = "123456789012"
        self.queue_name = "monocyte"

    def _create_sqs_queue(self):
        conn = boto3.client('sqs', region_name=self.queue_region)
        conn.create_queue(QueueName=self.queue_name)

    def _get_plugin(self):
        return AwsSQSPlugin([], [], True,
                            queue_account=self.queue_account,
                            queue_name=self.queue_name,
                            queue_region=self.queue_region)

    def _get_queue_url(self):
        sqs = boto3.client('sqs', region_name=self.queue_region)
        response = sqs.get_queue_url(QueueName=self.queue_name, QueueOwnerAWSAccountId=self.queue_account)
        return (sqs, response['QueueUrl'])

    @mock_sqs
    def test_plugin_send_message(self):
        self._create_sqs_queue()
        plugin = self._get_plugin()
        plugin.send_message("the body")

        (sqs, queue_url) = self._get_queue_url()
        messages = sqs.receive_message(QueueUrl=queue_url)['Messages']
        self.assertEqual(len(messages), 1)

        body = messages[0]['Body']
        self.assertEqual(body, "the body")

    def test_monocyte_status_no_issues(self):
        plugin = self._get_plugin()
        status = plugin.monocyte_status()
        self.assertEqual(status, "no issues")

    def test_monocyte_status_unwanted_and_problematic_resources(self):
        plugin = self._get_plugin()
        plugin.unwanted_resources = range(42)
        plugin.problematic_resources = range(123)
        status = plugin.monocyte_status()
        self.assertIn("42", status)
        self.assertIn("123", status)

    @patch('monocyte.plugins.sqs_plugin.AwsSQSPlugin._get_account_alias')
    @patch('monocyte.plugins.sqs_plugin.AwsSQSPlugin.monocyte_status')
    def test_get_body(self, mock_status, mock_alias):
        plugin = self._get_plugin()

        mock_status.return_value = "the status"
        mock_alias.return_value = "the alias"
        expected_body = {
            'status': mock_status.return_value,
            'account': mock_alias.return_value
        }

        self.assertEqual(json.loads(plugin.get_body()), expected_body)

    @patch('monocyte.plugins.sqs_plugin.AwsSQSPlugin.get_body')
    @patch('monocyte.plugins.sqs_plugin.AwsSQSPlugin.send_message')
    def test_run_with_no_errors(self, mock_send_message, mock_get_body):
        mock_get_body.return_value = "the body"

        plugin = self._get_plugin()
        plugin.run()

        mock_send_message.assert_called_with("the body")

    @patch('monocyte.plugins.sqs_plugin.AwsSQSPlugin.get_body')
    @patch('monocyte.plugins.sqs_plugin.AwsSQSPlugin.send_message')
    def test_run_logs_exceptions(self, mock_send_message, mock_get_body):
        message = "unit testing"
        mock_send_message.side_effect = Exception(message)

        plugin = self._get_plugin()
        with self.assertLogs(level=logging.WARN) as cm:
            plugin.run()

        logged_output = "\n".join(cm.output)
        self.assertRegex(logged_output, ".*run.*" + message)
