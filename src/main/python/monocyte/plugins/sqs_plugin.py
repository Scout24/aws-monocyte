from __future__ import print_function, absolute_import, division

import boto.sqs.message
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

    def _connect_to_queue(self):
        conn = boto.sqs.connect_to_region(self.queue_region)
        self.queue = conn.get_queue(self.queue_name, owner_acct_id=self.queue_account)
        if self.queue is None:
            raise "No queue '{0}' found in account '{1}', region '{2}'".format(
                  self.queue_name, self.queue_account, self.queue_region)

    def _get_account_alias(self):
        iam = boto.connect_iam()
        response = iam.get_account_alias()['list_account_aliases_response']
        return response['list_account_aliases_result']['account_aliases'][0]

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
        self._connect_to_queue()
        message = boto.sqs.message.RawMessage()
        message.set_body(body)
        self.queue.write(message)

    def run(self):
        try:
            self.send_message(self.get_body())
        except Exception as exc:
            self.logger.error("%s.run() failed to send to SQS: %s",
                              self.__class__.__name__, exc)
