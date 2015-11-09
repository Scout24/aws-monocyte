from ses_plugin import AwsSesPlugin


class StatusMailPlugin(AwsSesPlugin):
    def __init__(self, resources, region=None, sender=None, account_name=None, recipients=None):
        self.subject = 'AWS Compliance Checker - Your action is required'
        super(StatusMailPlugin, self).__init__(region, sender, recipients=recipients, subject=self.subject)
        self.resources = resources
        self.account_name = account_name

    @property
    def body(self):
        email_body = '''Dear AWS User,

our Compliance checker found some AWS resources outside of Europe in your account.
Please check and delete the following resources:

Account: {0}\n'''.format(self.account_name)

        regions = set([res.region for res in self.resources])
        res_types = set([res.resource_type for res in self.resources])

        for region in regions:
            region_text = "Region: {0}\n".format(region)
            email_body += region_text
            for res_type in res_types:
                selected_res = (resource for resource in self.resources
                                if resource.region == region and resource.resource_type == res_type)
                for resource in selected_res:
                    res_text = "\t{0} instance with identifier {1}, created {2}\n".format(
                        res_type, resource.resource_id, resource.creation_date)
                    email_body += res_text
        email_footer = '\n Kind regards.\n\tYour Compliance Team'
        email_body += email_footer

        return email_body

    def run(self):
        if self.resources:
            self.send_email()
