from __future__ import print_function, absolute_import, division

import boto3
import json

from .ses_plugin import AwsSesPlugin


class StatusMailPlugin(AwsSesPlugin):
    def __init__(self, unwanted_resources, problematic_resources, dry_run, **kwargs):
        self.subject = 'AWS Compliance Checker - Your action is required'
        super(StatusMailPlugin, self).__init__(unwanted_resources, problematic_resources, dry_run, subject=self.subject, **kwargs)

    @property
    def body(self):
        if self.dry_run:
            unwanted_resources_info = "Please check the following resources:"
        else:
            unwanted_resources_info = "Please check the following deleted resources:"
        email_body = '''Dear AWS User,

our Compliance checker found some issues in your account.
{0}

Account: {1}\n'''.format(unwanted_resources_info, self._get_account_alias())

        email_body += self._handle_resources(self.unwanted_resources)

        if self.problematic_resources:
            email_body += ("\nAdditionally we had issues checking the following "
                           "resource, please ensure that they are in the proper region:\n")
            email_body += self._handle_resources(self.problematic_resources)

        email_footer = '\n Kind regards.\n\tYour Compliance Team'
        email_body += email_footer

        return email_body

    def _handle_resources(self, resources):
        return_text = ""
        regions = sorted(list(set([res.region for res in resources])))
        res_types = sorted(list(set([res.resource_type for res in resources])))

        for region in regions:
            region_text = "Region: {0}\n".format(region)
            return_text += region_text
            for res_type in res_types:
                selected_res = (resource for resource in resources
                                if resource.region == region and resource.resource_type == res_type)
                for resource in selected_res:
                    res_text = "\t{0} with identifier {1}, created {2}.".format(
                        res_type, resource.resource_id, resource.creation_date)
                    if resource.reason:
                        res_text += ' ' + resource.reason
                    res_text += '\n'
                    return_text += res_text
        return return_text or "\tNone\n"

    def _get_account_alias(self):
        iam = boto3.client('iam')
        response = iam.list_account_aliases()
        return response['AccountAliases'][0]

    def run(self):
        if self.unwanted_resources or self.problematic_resources:
            self.send_email()


class UsofaStatusMailPlugin(StatusMailPlugin):
    """StatusMailPlugin that finds additional recipients via usofa"""
    def __init__(self, unwanted_resources, problematic_resources, dry_run, usofa_bucket_name=None, **kwargs):
        super(UsofaStatusMailPlugin, self).__init__(unwanted_resources, problematic_resources, dry_run, **kwargs)
        self.usofa_bucket_name = usofa_bucket_name

    def _get_usofa_data(self):
        s3 = boto3.client('s3', region_name=self.region)
        response = s3.get_object(Bucket=self.usofa_bucket_name, Key='accounts.json')
        account_data = json.loads(response['Body'].read().decode('utf-8'))
        return account_data

    @property
    def recipients(self):
        usofa = self._get_usofa_data()
        account_alias = self._get_account_alias()
        responsible = usofa[account_alias]['email']

        if self.mail_recipients:
            recipients = list(self.mail_recipients)
            recipients.append(responsible)
            return recipients
        return [responsible]
