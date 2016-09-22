from __future__ import print_function, absolute_import, division

import boto3
import logging
from monocyte.handler import Resource, Handler


class User(Handler):

    def get_users(self):
        client = boto3.client('iam')
        user_response = client.list_users()
        users = user_response['Users']
        return users

    def check_users(self, users):
        if not users:
            return True
        blacklist = {'arn:aws:iam::123456789:user/test1', 'arn:aws:iam::123456789:user/test3',
                     'arn:aws:iam::123456789:user/test5'}
        for user in users:
            if user['Arn'] not in blacklist:
                return False
        return False

