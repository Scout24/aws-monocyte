from __future__ import print_function, absolute_import, division

import boto3
from boto import iam
from monocyte.handler import Resource, Handler
from six import string_types


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

    def gather_actions(self, policy_document):
        if not isinstance(policy_document['Statement'], list):
            if isinstance(policy_document['Statement']['Action'], list):
                return policy_document['Statement']['Action']
            return [policy_document['Statement']['Action']]
        statement = policy_document['Statement']
        actions = []
        for action in statement:
            if isinstance(action['Action'], list):
                for inner_action in action['Action']:
                    actions.append(inner_action)
            else:
                actions.append(action['Action'])
        return actions

    def check_policy_action_for_forbidden_string(self, actions):
        if isinstance(actions, string_types):
            actions = [actions]
        if '*:*' in actions or '*' in actions:
            return True
        return False

    def check_policy_resource_for_forbidden_string(self, actions, resources):
        if isinstance(actions, string_types):
            actions = [actions]
        for action in actions:
            if action.startswith('elasticloadbalancing:'):
                return False
        if isinstance(resources, string_types):
            resources = [resources]
        for resource in resources:
            if '*' == resource:
                return True
        return False

    def is_arn_in_whitelist(self, policy):
        whitelist_arns = self.get_whitelist().get('Arns', [])
        for arn_with_reason in whitelist_arns:
            if policy['Arn'] == arn_with_reason['Arn']:
                return True
        return False

    def delete(self, resource):
        if self.dry_run:
            return
        raise NotImplementedError("Should have implemented this")

    def get_policy_resource(self, policy_document):
        statement = policy_document['Statement']
        if not isinstance(statement, list):
            resources = statement['Resource']
            return resources
        return statement[0]['Resource']

class IamPolicy(Policy):
    def get_policies(self):
        client = boto3.client('iam')
        return client.list_policies(Scope='Local')['Policies']

    def get_policy_document(self, arn, version):
        resource = boto3.resource('iam')
        return resource.PolicyVersion(arn, version).document

    def fetch_unwanted_resources(self):
        for policy in self.get_policies():
            if self.is_arn_in_whitelist(policy):
                continue
            policy_document = self.get_policy_document(policy['Arn'], policy['DefaultVersionId'])
            actions = self.gather_actions(policy_document)
            resources = self.get_policy_resource(policy_document)
            if self.check_policy_action_for_forbidden_string(actions) or self.check_policy_resource_for_forbidden_string(actions, resources):
                unwanted_resource = Resource(resource=policy,
                                             resource_type=self.resource_type,
                                             resource_id=policy['Arn'],
                                             creation_date=policy['CreateDate'],
                                             region='global')
                yield unwanted_resource

    def to_string(self, resource):
        return "Not allowed policy found {0}".format(resource.resource_id)


class InlinePolicy(Policy):
    def get_all_iam_roles_in_account(self):
        client = boto3.client('iam')
        roles_response = client.list_roles()['Roles']
        return roles_response

    def get_all_inline_policies_for_role(self, role_name):
        iam = boto3.resource('iam')
        role_policies = []
        role = iam.Role(role_name)
        for role_policy in role.policies.all():
            role_policies.append(role_policy)
        return role_policies


    def fetch_unwanted_resources(self):
        for role in self.get_all_iam_roles_in_account():
            if self.is_arn_in_whitelist(role):
                continue
            policy_names = self.get_all_inline_policies_for_role(role['RoleName'])
            for policy in policy_names:
                resources = self.get_policy_resource(policy.policy_document)
                actions = self.gather_actions(policy.policy_document)
                if self.check_policy_action_for_forbidden_string(
                        actions) or self.check_policy_resource_for_forbidden_string(actions, resources):
                    unwanted_resource = Resource(resource=role,
                                                 resource_type=self.resource_type,
                                                 resource_id=role['Arn'],
                                                 creation_date=role['CreateDate'],
                                                 region='global')
                    yield unwanted_resource

    def is_arn_in_whitelist(self, role):
        whitelist_arns = self.get_whitelist().get('Arns', [])
        for arn_with_reason in whitelist_arns:
            if role['Arn'] == arn_with_reason['Arn']:
                return True
        return False

    def to_string(self, resource):
        return "Role with not allowed inline policy found {0}".format(resource.resource_id)
