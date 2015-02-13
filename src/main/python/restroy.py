#!/usr/bin/env python
import boto


class Restroy(object):

    def __init__(self):
        self.services = ['awslambda', 'beanstalk', 'cloudformation', 'cloudformation', 'cloudhsm', 'cloudsearch',
                         'cloudsearch2', 'cloudsearchdomain', 'cloudtrail', 'codedeploy', 'cognito.identity',
                         'cognito.sync', 'configservice', 'datapipeline', 'dynamodb', 'dynamodb2', 'ec2.autoscale',
                         'ec2.cloudwatch', 'ec2.elb', 'ec2', 'ec2.containerservice', 'elasticache', 'elastictranscoder',
                         'emr', 'glacier', 'iam', 'kinesis', 'kms', 'logs', 'opsworks', 'rds', 'rds2', 'redshift',
                         'route53.domains', 's3', 'sdb', 'ses', 'sns', 'sqs', 'sts', 'support', 'swf', 'vpc']

    def delete_resources(self, whitelist=None):
        if not whitelist:
            whitelist = ['eu-west-1', 'eu-central-1']

        print 'Region Whiteliste: [{0}]'.format(', '.join(whitelist))

        for service in self.services:
            regions = self._fetch_regions_by_service(service)
            if not regions:
                continue
            for region in regions:
                if region.name in whitelist:
                    continue
                resources_in_region = self._fetch_resources_by_region(region)
                self._destroy_resources(resources_in_region)

    def _fetch_regions_by_service(self, service):
        regions = None
        module_identifier = 'boto.%s' % service

        try:
            __import__(module_identifier)
            regions = eval(module_identifier + '.regions()')
            print 'Fetched regions for {0}: {1}'.format(service, (lambda x: x if regions else 0)(len(regions)))
        except ImportError:
            print 'Could not import ' + module_identifier

        return regions

    def _fetch_resources_by_region(self, region):
        # TODO implement identifying resources
        return []

    def _destroy_resources(self, resources):
        # TODO implement destroying resources
        return 0

if __name__ == '__main__':
    cleanup = Restroy()
    cleanup.delete_resources()