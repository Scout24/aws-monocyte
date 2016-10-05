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

class Policy(Handler):
    def fetch_regions(self):
        return iam.regions()

    def show_action(self, policy_document):
        return policy_document['Statement'][0]['Action']

    def check_action(self, policy_document):
        for action in self.show_action(policy_document):
            #print(action)
            if action == "*.*":
                return True
        return False

    def is_policy_in_whitelist(self, policy):
        whitelist_arns = self.get_whitelist().get('Arns', [])
        for arn_with_reason in whitelist_arns:
            if policy['Arn'](policy) == arn_with_reason['Arn']:
                return True
        return False

    def to_string(self, resource):
        return "unallowed policy action found {0}".format(resource.resource_id)

    def delete(self, resource):
        if self.dry_run:
            return
        raise NotImplementedError("Should have implemented this")



class PolicyPolicy(Policy):

    def get_policies(self):
        client = boto3.client('iam')
        return client.list_policies(Scope='Local')['Policies']

    def get_policy_document(self, arn, version):
        resource = boto3.resource('iam')
        return resource.PolicyVersion(arn, version).document

    def fetch_unwanted_resources(self):
        for policy in self.get_policies():
            if self.is_policy_in_whitelist(policy):
                continue
            if self.check_action(self.get_policy_document(policy['Arn'], policy['DefaultVersionId'])):
                unwanted_resource = Resource(resource=policy,
                                             resource_type=self.resource_type,
                                             resource_id=policy['Arn'],
                                             creation_date=policy['CreateDate'],
                                             region='global')
                yield unwanted_resource

