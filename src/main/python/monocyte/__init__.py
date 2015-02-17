from __future__ import print_function

import boto


class Monocyte(object):

    OK = 0

    def __init__(self, blacklisted=None):
#        self.services = ['awslambda', 'beanstalk', 'cloudformation', 'cloudformation', 'cloudhsm', 'cloudsearch',
#                         'cloudsearch2', 'cloudsearchdomain', 'cloudtrail', 'codedeploy', 'cognito.identity',
#                         'cognito.sync', 'configservice', 'datapipeline', 'dynamodb', 'dynamodb2', 'ec2.autoscale',
#                         'ec2.cloudwatch', 'ec2.elb', 'ec2', 'ec2.containerservice', 'elasticache', 'elastictranscoder',
#                         'emr', 'glacier', 'iam', 'kinesis', 'kms', 'logs', 'opsworks', 'rds', 'rds2', 'redshift',
#                         'route53.domains', 's3', 'sdb', 'ses', 'sns', 'sqs', 'sts', 'support', 'swf', 'vpc']
        self.services = ["ec2"]
        self.blacklisted = blacklisted if blacklisted else ['eu-west-1', 'eu-central-1']

        print('Blacklisted regions: [{0}]'.format(', '.join(self.blacklisted)))


    def search_and_destroy_unwanted_resources(self):
        for service in self.services:
            boto_module, regions = self._fetch_regions_by_service(service)
            if not regions:
                continue
            for region in regions:
                if region.name in self.blacklisted:
                    #print("\tBlacklisted, thus skipped")
                    continue
                resources_in_region = self._fetch_resources_by_region(boto_module, region)
                #self._destroy_resources(resources_in_region)

        return Monocyte.OK

    def _fetch_regions_by_service(self, service):
        regions = None
        module_identifier = 'boto.%s' % service

        try:
            boto_module = __import__(module_identifier, globals(), locals(), [service])
            regions = boto_module.regions()
            regions = regions if regions else []
            print('Fetched regions for {0}: {1}'.format(service, len(regions)))
        except ImportError:
            print('Could not import ' + module_identifier)
            raise

        return (boto_module, regions)

    def _fetch_resources_by_region(self, mod, region):
        connection = mod.connect_to_region(region.name)
        instances = []

        try:
            instances = connection.get_only_instances()
            for instance in instances:
                print("instance found in {region.name}\n\t{id} [{image_id}] - {instance_type}, since {launch_time}\n\tip {public_dns_name}, key {key_name}".format(**vars(instance)))  # TODO more generic
        except BaseException as e:
            print(e)
            raise

        return instances

    def _destroy_resources(self, resources):
        # TODO implement destroying resources
        return 0
