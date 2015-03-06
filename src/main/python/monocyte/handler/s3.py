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


import boto
from boto.exception import S3ResponseError
from monocyte.handler import Resource, Handler

US_STANDARD_REGION = "us-east-1"


class Bucket(Handler):
    NR_KEYS_TO_SHOW = 4

    def fetch_regions(self):
        return []

    def fetch_unwanted_resources(self):
        for bucket in boto.connect_s3().get_all_buckets():
            try:
                region = bucket.get_location()
            except S3ResponseError as e:
                # See https://github.com/boto/boto/issues/2741
                if e.status == 400:
                    self.logger.info("\twarning: get_location() crashed for %s, skipping" % bucket.name)
                    continue
                region = "__error__"
            region = region if region else US_STANDARD_REGION
            if self.region_filter(region):
                yield Resource(bucket, region)

    def to_string(self, resource):
        return "s3 bucket found in {0}\n\t{1}, created {2}".format(resource.region,
                                                                   resource.wrapped.name,
                                                                   resource.wrapped.creation_date)

    def delete(self, resource):
        if self.dry_run:
            nr_keys = len(resource.wrapped.get_all_keys())
            self.logger.info("\t{0} entries would be removed:".format(nr_keys))
            self.logger.warn("s3 bucket {0} would be removed because its available in unwanted region {1}".format(
                    resource.wrapped.name, resource.region))
            if nr_keys:
                for nr, key in enumerate(resource.wrapped.list()):
                    if nr >= Bucket.NR_KEYS_TO_SHOW:
                        self.logger.info("\t... ({0} keys omitted)".format(nr_keys - Bucket.NR_KEYS_TO_SHOW))
                        break
                    self.logger.info("\tkey '{0}'".format(key.name))
            return
        delete_keys_result = resource.wrapped.delete_keys(resource.wrapped.list())
        self.logger.info("\tInitiating deletion sequence")
        self.logger.warn("s3 bucket {0} gets removed because its available in unwanted region {1}".format(
                resource.wrapped.name, resource.region))

        delete_bucket_result = boto.connect_s3().delete_bucket(resource.wrapped.name)
        return delete_keys_result, delete_bucket_result
