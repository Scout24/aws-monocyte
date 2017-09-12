# Monocyte - Search and Destroy unwanted AWS Resources relentlessly.
# Copyright 2015 Immobilien Scout GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import boto3
from monocyte.handler import Resource, Handler

US_STANDARD_REGION = "us-east-1"
SIGV4_REGIONS = ['eu-central-1']
AVAILABILITY_ZONES = {'EU': 'eu-west-1', None: US_STANDARD_REGION}


class Bucket(Handler):
    def map_location(self, region):
        return AVAILABILITY_ZONES.get(region, region)

    def get_client(self):
        return boto3.client('s3', region_name='eu-central-1')

    def fetch_region_names(self):
        session = boto3.session.Session()
        return session.get_available_regions('s3')

    def fetch_unwanted_resources(self):
        client = self.get_client()
        response = client.list_buckets()
        buckets = [(bucket['Name'], bucket['CreationDate'])
                   for bucket in response['Buckets']]

        for bucket_name, creation_date in buckets:
            try:
                response = client.get_bucket_location(Bucket=bucket_name)
            except Exception:
                # This happens when a bucket was deleted shortly after we
                # found it. E.g. during concurrent integration tests.
                self.logger.exception("Failed to get location for bucket %r:",
                                      bucket_name)
                continue
            region_name = self.map_location(response['LocationConstraint'])
            if region_name not in self.region_names or self.is_on_whitelist(bucket_name):
                self.logger.debug("Bucket %s in region %s is OK.",
                                  bucket_name, region_name)
                continue

            self.logger.info("Reporting bucket %s in region %s as unwanted.",
                             bucket_name, region_name)
            resource_wrapper = Resource(
                resource="Bucket " + bucket_name,
                resource_type=self.resource_type,
                resource_id=bucket_name,
                creation_date=creation_date,
                region=region_name)
            yield resource_wrapper

    def to_string(self, resource):
        return "s3 bucket found in {0}, with name {1}, created {2}".format(
            resource.region, resource.resource_id, resource.creation_date)

    def is_on_whitelist(self, bucket_name):
        bucket_arn = "arn:aws:s3:::%s" % bucket_name
        whitelist_arns = self.get_whitelist().get('Arns', [])
        for arn_with_reason in whitelist_arns:
            if bucket_arn == arn_with_reason['Arn']:
                return True

        return False

    def delete(self, resource):
        if self.dry_run:
            return

        if isinstance(resource, Resource):
            bucket_name = resource.resource_id
        else:
            bucket_name = resource
        client = self.get_client()

        while True:
            response = client.list_objects_v2(Bucket=bucket_name)
            if response['KeyCount'] == 0:
                break
            keys = [item['Key'] for item in response['Contents']]
            delete_spec = {'Objects': [{'Key': key} for key in keys]}
            client.delete_objects(Bucket=bucket_name, Delete=delete_spec)
        try:
            client.delete_bucket(Bucket=bucket_name)
        except Exception:
            self.logger.exception("Failed to delete bucket %r:" % resource)
            raise
