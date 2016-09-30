from __future__ import print_function, absolute_import, division

from monocyte.handler import Resource, Handler
import boto3
from boto import iam

class User(Handler):

    def fetch_regions(self):
        return iam.regions()

    def get_users(self):
        iam = boto3.client('iam')
        user_response = iam.list_users()
        return user_response['Users']

    def fetch_unwanted_resources(self):
        for user in self.get_users():
            if self.is_user_in_whitelist(user) or self.is_user_in_ignored_resources(user):
                self.logger.info('IGNORE user with {0}'.format(user['Arn']))
                continue

            unwanted_resource = Resource(resource=user,
                                         resource_type=self.resource_type,
                                         resource_id=user['Arn'],
                                         creation_date=user['CreateDate'],
                                         region='global')
            yield unwanted_resource

    def is_user_in_whitelist(self, user):
        whitelist_arns = self.get_whitelist().get('Arns', [])
        for arn_with_reason in whitelist_arns:
            if user['Arn'] == arn_with_reason['Arn']:
                return True

        return False

    def is_user_in_ignored_resources(self, user):
        return user['Arn'] in self.ignored_resources

    def to_string(self, resource):
        return "iam user found {0}".format(resource.resource_id)

    def delete(self, resource):
        if self.dry_run:
            return
        raise NotImplementedError("Should have implemented this")

