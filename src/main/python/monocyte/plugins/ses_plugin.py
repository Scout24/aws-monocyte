from __future__ import print_function, absolute_import, division

import boto3
import logging


class AwsSesPlugin(object):

    def __init__(self, unwanted_resources, problematic_resources, dry_run, region=None, sender=None, subject=None,
                 recipients=None, body=None):
        self.region = region
        self.mail_sender = sender
        self.subject = subject
        self.mail_recipients = recipients or []
        self.mail_body = body
        self.unwanted_resources = unwanted_resources
        self.problematic_resources = problematic_resources
        self.dry_run = dry_run
        self.logger = logging.getLogger(__name__)

    @property
    def sender(self):
        return self.mail_sender

    @property
    def recipients(self):
        return self.mail_recipients

    @property
    def body(self):
        return self.mail_body

    def send_email(self):
        conn = boto3.client('ses', region_name=self.region)

        self.logger.info("Sending Email to %s", ", ".join(self.recipients))

        conn.send_email(
            Source=self.sender,
            Destination={'ToAddresses': [self.sender]},
            Message={
                'Subject': {
                    'Data': self.subject
                },
                'Body': {
                    'Text': {
                        'Data': self.body
                    }
                }
            })

    def run(self):
        self.send_email()
