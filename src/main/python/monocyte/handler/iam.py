from __future__ import print_function, absolute_import, division

from monocyte.handler import Resource, Handler
import boto3

class User(Handler):

    def fetch_regions(self):
        return []

    def get_users(self):
        iam = boto3.resource('iam')
        user_response = iam.list_users()
        return user_response['Users']

    def fetch_unwanted_resources(self):
        for user in self.get_users():
            unwanted_resource = Resource(resource=user,
                                        resource_type=self.resource_type,
                                        resource_id=user['Arn'],
                                        creation_date=user['CreateDate'])
            yield unwanted_resource
