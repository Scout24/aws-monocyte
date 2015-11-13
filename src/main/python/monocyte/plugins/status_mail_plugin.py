from __future__ import print_function, absolute_import, division

import boto

from .ses_plugin import AwsSesPlugin


class StatusMailPlugin(AwsSesPlugin):
    def __init__(self, resources, **kwargs):
        self.subject = 'AWS Compliance Checker - Your action is required'
        super(StatusMailPlugin, self).__init__(resources, **kwargs)

    @property
    def body(self):
        email_body = '''Dear AWS User,

our Compliance checker found some AWS resources outside of Europe in your account.
Please check and delete the following resources:

Account: {0}\n'''.format(self._get_account_alias())

        regions = sorted(list(set([res.region for res in self.resources])))
        res_types = sorted(list(set([res.resource_type for res in self.resources])))

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

    def _get_account_alias(self):
        iam = boto.connect_iam()
        response = iam.get_account_alias()['list_account_aliases_response']
        return response['list_account_aliases_result']['account_aliases'][0]


    def run(self):
        if self.resources:
            self.send_email()
