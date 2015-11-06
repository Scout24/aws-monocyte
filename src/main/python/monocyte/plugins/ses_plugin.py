from boto import ses


class AwsSesPlugin(object):

    def __init__(self, region, sender=None, subject=None, recipients=None, body=None):
        self.region = region
        self.mail_sender = sender
        self.subject = subject
        self.mail_recipients = recipients
        self.mail_body = body

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
        conn = ses.connect_to_region(
            region_name=self.region,
            aws_access_key_id='XXX',
            aws_secret_access_key='XXX',
            security_token='XXXX'
        )
        conn.send_email(
            source=self.sender,
            subject='AWS Compliance Checker - Your action is required',
            body=self.body,
            to_addresses=self.recipients)
