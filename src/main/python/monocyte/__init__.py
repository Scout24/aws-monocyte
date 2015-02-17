from __future__ import print_function

import boto


class Monocyte(object):

    OK = 0

    def __init__(self):
#        self.services = ['awslambda', 'beanstalk', 'cloudformation', 'cloudformation', 'cloudhsm', 'cloudsearch',
#                         'cloudsearch2', 'cloudsearchdomain', 'cloudtrail', 'codedeploy', 'cognito.identity',
#                         'cognito.sync', 'configservice', 'datapipeline', 'dynamodb', 'dynamodb2', 'ec2.autoscale',
#                         'ec2.cloudwatch', 'ec2.elb', 'ec2', 'ec2.containerservice', 'elasticache', 'elastictranscoder',
#                         'emr', 'glacier', 'iam', 'kinesis', 'kms', 'logs', 'opsworks', 'rds', 'rds2', 'redshift',
#                         'route53.domains', 's3', 'sdb', 'ses', 'sns', 'sqs', 'sts', 'support', 'swf', 'vpc']
        self.services = ["ec2"]

    def search_and_destroy_unwanted_resources(self, blacklisted=None):
        if not blacklisted:
            blacklisted = ['eu-west-1', 'eu-central-1']

        print('Blacklisted regions: [{0}]'.format(', '.join(blacklisted)))

        for service in self.services:
            regions = self._fetch_regions_by_service(service)
            if not regions:
                continue
            for region in regions:
                print("Checking %s" % region)
                if region.name in blacklisted:
                    print("\tBlacklisted, thus skipped")
                    continue
                resources_in_region = self._fetch_resources_by_region(region)
                #self._destroy_resources(resources_in_region)

        return Monocyte.OK

    def _fetch_regions_by_service(self, service):
        regions = None
        module_identifier = 'boto.%s' % service

        try:
            __import__(module_identifier)
            regions = eval(module_identifier + '.regions()')
            print('Fetched regions for {0}: {1}'.format(service, (lambda x: x if regions else 0)(len(regions))))
        except ImportError:
            print('Could not import ' + module_identifier)

        return regions

    def _fetch_resources_by_region(self, region):
        print("Region: %s" % region.name)

        connection = boto.ec2.connect_to_region(region.name)  # TODO: more generic
        instances = []

        try:
            instances = connection.get_only_instances()
            for instance in instances:
                print("\t%s" % instance)
        except BaseException as e:
            print(e)
            raise

        return instances

    def _destroy_resources(self, resources):
        # TODO implement destroying resources
        return 0
