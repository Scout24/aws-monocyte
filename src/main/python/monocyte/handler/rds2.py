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

SKIPPING_STATEMENT = "\tDeletion already in progress. Skipping."
DELETION_STATEMENT = "\tInitiating deletion sequence."
DRY_RUN_STATEMENT = "\tDRY RUN: Would be deleted otherwise."

DELETING_STATUS = "deleting"


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
            print(DRY_RUN_STATEMENT)
            return
        if resource.wrapped["DBInstanceStatus"] == DELETING_STATUS:
            print(SKIPPING_STATEMENT)
            return
        print(DELETION_STATEMENT)
        connection = boto.rds2.connect_to_region(resource.region)
        response = connection.delete_db_instance(resource.wrapped["DBInstanceIdentifier"], skip_final_snapshot=True)
        return response["DeleteDBInstanceResponse"]["DeleteDBInstanceResult"]["DBInstance"]


class Snapshot(Handler):

    def fetch_regions(self):
        return boto.rds2.regions()

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
        if self.dry_run:
            print(DRY_RUN_STATEMENT)
            return
        if resource.wrapped["Status"] == DELETING_STATUS:
            print(SKIPPING_STATEMENT)
            return
        if resource.wrapped["SnapshotType"] == "automated":
            print("\tNot a manually created Snapshot. Skipping.")
            return
        print(DELETION_STATEMENT)
        connection = boto.rds2.connect_to_region(resource.region)
        response = connection.delete_db_snapshot(resource.wrapped["DBSnapshotIdentifier"])
        return response
