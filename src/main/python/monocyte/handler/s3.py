# Monocyte - An AWS Resource Destroyer
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

from __future__ import print_function

import boto
import boto.ec2
from boto.exception import S3ResponseError
from monocyte.handler import Resource, Handler, aws_handler

US_STANDARD_REGION = "us-east-1"


@aws_handler
class Handler(Handler):
    NR_KEYS_TO_SHOW = 4

    def __init__(self, region_filter, dry_run=True):
        self.region_filter = region_filter
        self.dry_run = dry_run
        self.name = __name__.rsplit(".", 1)[1]
        self.connection = boto.connect_s3()

    def fetch_unwanted_resources(self):
        for bucket in self.connection.get_all_buckets():
            try:
                region = bucket.get_location()
            except S3ResponseError as e:
                # See https://github.com/boto/boto/issues/2741
                if e.status == 400:
                    print("\twarning: get_location() crashed for %s, skipping" % bucket.name)
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
            print("\t{} entries would be removed:".format(nr_keys))
            if nr_keys:
                for nr, key in enumerate(resource.wrapped.list()):
                    if nr >= Handler.NR_KEYS_TO_SHOW:
                        print("\t... (skip remaining {} keys)".format(nr_keys - Handler.NR_KEYS_TO_SHOW))
                        break
                    print("\tkey '{}'".format(key.name))
            return
        delete_keys_result = resource.wrapped.delete_keys(resource.wrapped.list())
        print("\tInitiating deletion sequence")
        delete_bucket_result = self.connection.delete_bucket(resource.wrapped.name)
        return delete_keys_result, delete_bucket_result
