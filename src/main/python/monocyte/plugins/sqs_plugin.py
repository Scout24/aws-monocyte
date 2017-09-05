from __future__ import print_function, absolute_import, division

import boto3
import json
import logging


class AwsSQSPlugin(object):

    def __init__(self, unwanted_resources, problematic_resources, dry_run,
                 queue_account=None, queue_name=None, queue_region=None,):
        self.queue_account = queue_account
        self.queue_name = queue_name
        self.queue_region = queue_region
        self.unwanted_resources = unwanted_resources
        self.problematic_resources = problematic_resources
        self.dry_run = dry_run

        self.logger = logging.getLogger(__name__)

    def _get_account_alias(self):
        iam = boto3.client('iam')
        response = iam.list_account_aliases()
        return response['AccountAliases'][0]

    def monocyte_status(self):
        if self.unwanted_resources or self.problematic_resources:
            return "Found {0} unwanted and {1} problematic resources.".format(
                len(self.unwanted_resources), len(self.problematic_resources)
            )
        return "no issues"

    def get_body(self):
        body = {
            'status': self.monocyte_status(),
            'account': self._get_account_alias()
        }
        return json.dumps(body)

    def send_message(self, body):
        sqs = boto3.client('sqs', region_name=self.queue_region)
        response = sqs.get_queue_url(QueueName=self.queue_name, QueueOwnerAWSAccountId=self.queue_account)
        sqs.send_message(QueueUrl=response['QueueUrl'], MessageBody=body)

    def run(self):
        try:
            self.send_message(self.get_body())
        except Exception as exc:
            self.logger.error("%s.run() failed to send to SQS: %s",
                              self.__class__.__name__, exc)
