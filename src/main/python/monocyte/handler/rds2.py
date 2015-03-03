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
import boto.rds2
from monocyte.handler import Resource, Handler


class Instance(Handler):

    def fetch_regions(self):
        return boto.rds2.regions()

    def fetch_unwanted_resources(self):
        for region in self.regions:
            connection = boto.rds2.connect_to_region(region.name)
            resources = connection.describe_db_instances() or []
            for resource in resources["DescribeDBInstancesResponse"]["DescribeDBInstancesResult"]["DBInstances"]:
                yield Resource(resource, region.name)

    def to_string(self, resource):
        return "Database Instance found in {region} \n\t".format(**vars(resource)) + \
               "{DBInstanceIdentifier}, status {DBInstanceStatus}".format(**resource.wrapped)

    def delete(self, resource):
        if self.dry_run:
            print("\tDry Run: Would be deleted otherwise.")
            return
        if resource.wrapped["DBInstanceStatus"] == "deleting":
            print("\tDeletion already in progress. Skipping.")
            return
        print("\tInitiating deletion sequence.")
        connection = boto.rds2.connect_to_region(resource.region)
        response = connection.delete_db_instance(resource.wrapped["DBInstanceIdentifier"], skip_final_snapshot=True)
        return response["DeleteDBInstanceResponse"]["DeleteDBInstanceResult"]["DBInstance"]


class Snapshot(Handler):

    def __init__(self, region_filter, dry_run=True):
        self.regions = [region for region in boto.rds2.regions() if region_filter(region.name)]
        self.dry_run = dry_run

    def fetch_unwanted_resources(self):
        for region in self.regions:
            connection = boto.rds2.connect_to_region(region.name)
            resources = connection.describe_db_snapshots() or []
            for resource in resources["DescribeDBSnapshotsResponse"]["DescribeDBSnapshotsResult"]["DBSnapshots"]:
                yield Resource(resource, region.name)

    def to_string(self, resource):
        return "Database Snapshot found in {region} \n\t".format(**vars(resource)) + \
               "{DBSnapshotIdentifier}, status {Status}".format(**resource.wrapped)

    def delete(self, resource):
        pass
