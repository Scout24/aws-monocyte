from __future__ import print_function, absolute_import, division

from boto import ses


class AwsSesPlugin(object):

    def __init__(self, resources, region=None, sender=None, subject=None,
                 recipients=None, body=None):
        self.region = region
        self.mail_sender = sender
        self.subject = subject
        self.mail_recipients = recipients or []
        self.mail_body = body
        self.resources = resources

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
        conn = ses.connect_to_region(region_name=self.region)

        conn.send_email(
            source=self.sender,
            subject=self.subject,
            body=self.body,
            to_addresses=self.recipients)

    def run(self):
        self.send_email()
