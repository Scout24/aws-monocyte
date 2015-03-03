# Monocyte - An AWS Resource Destroyer
# Copyright 2015 Immobilien Scout GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import boto.rds2
import boto.regioninfo
from unittest import TestCase
from mock import patch, Mock
from monocyte.handler import rds2, Resource


class RDSInstanceTest(TestCase):
    def setUp(self):
        self.boto_mock = patch("monocyte.handler.rds2.boto").start()
        self.instance_mock = self._given_instance_mock()

        self.positive_fake_region = Mock(boto.regioninfo.RegionInfo)
        self.positive_fake_region.name = "allowed_region"
        self.negative_fake_region = Mock(boto.regioninfo.RegionInfo)
        self.negative_fake_region.name = "forbidden_region"
        self.boto_mock.rds2.regions.return_value = [self.positive_fake_region, self.negative_fake_region]
        self.rds_instance = rds2.Instance(lambda region_name: True)

    def tearDown(self):
        patch.stopall()

    def test_fetch_unwanted_resources_filtered(self):
        self.boto_mock.rds2.connect_to_region.return_value.describe_db_instances.return_value = \
            self._given_db_instances_response()

        only_resource = list(self.rds_instance.fetch_unwanted_resources())[0]
        self.assertEquals(only_resource.wrapped, self.instance_mock)

    def test_to_string(self):
        self.boto_mock.rds2.connect_to_region.return_value.describe_db_instances.return_value = \
            self._given_db_instances_response()

        only_resource = list(self.rds_instance.fetch_unwanted_resources())[0]
        resource_string = self.rds_instance.to_string(only_resource)

        self.assertTrue(self.instance_mock["DBInstanceIdentifier"] in resource_string)
        self.assertTrue(self.instance_mock["DBInstanceStatus"] in resource_string)

    @patch("monocyte.handler.rds2.print", create=True)
    def test_skip_deletion_in_dry_run(self, print_mock):
        self.rds_instance.dry_run = True
        resource = Resource(self.instance_mock, self.negative_fake_region.name)

        deleted_resource = self.rds_instance.delete(resource)
        print_mock.assert_called_with(rds2.DRY_RUN_STATEMENT)
        self.assertEquals(None, deleted_resource)

    @patch("monocyte.handler.rds2.print", create=True)
    def test_skip_deletion_if_already_deleted(self, print_mock):
        self.rds_instance.dry_run = False
        self.instance_mock["DBInstanceStatus"] = rds2.DELETING_STATUS

        resource = Resource(self.instance_mock, self.negative_fake_region.name)

        deleted_resource = self.rds_instance.delete(resource)
        print_mock.assert_called_with(rds2.SKIPPING_STATEMENT)
        self.assertEquals(None, deleted_resource)

    @patch("monocyte.handler.rds2.print", create=True)
    def test_does_delete_if_not_dry_run(self, print_mock):
        self.rds_instance.dry_run = False

        resource = Resource(self.instance_mock, self.negative_fake_region.name)

        self.boto_mock.rds2.connect_to_region.return_value.delete_db_instance.return_value = \
            self._given_delete_db_instance_response()

        deleted_resource = self.rds_instance.delete(resource)
        print_mock.assert_called_with("\tInitiating deletion sequence.")
        self.assertEquals(self.instance_mock["DBInstanceIdentifier"], deleted_resource["DBInstanceIdentifier"])
        self.assertEquals("deleting", deleted_resource["DBInstanceStatus"])

    def _given_db_instances_response(self):
        return {
            'DescribeDBInstancesResponse': {
                'DescribeDBInstancesResult': {
                    'DBInstances': [self.instance_mock]
                }
            }
        }

    def _given_instance_mock(self):
        return {
            "DBInstanceIdentifier": "myInstanceIdentifier",
            "DBInstanceStatus": "myStatus"
        }

    def _given_delete_db_instance_response(self):
        return {
            "DeleteDBInstanceResponse": {
                "DeleteDBInstanceResult": {
                    "DBInstance": {
                        "DBInstanceStatus": "deleting",
                        "DBInstanceIdentifier": self.instance_mock["DBInstanceIdentifier"]
                    }
                }
            }
        }


class RDSSnapshotTest(TestCase):
    def setUp(self):
        self.boto_mock = patch("monocyte.handler.rds2.boto").start()
        self.snapshot_mock = self._given_snapshot_mock()

        self.positive_fake_region = Mock(boto.regioninfo.RegionInfo)
        self.positive_fake_region.name = "allowed_region"
        self.negative_fake_region = Mock(boto.regioninfo.RegionInfo)
        self.negative_fake_region.name = "forbidden_region"
        self.boto_mock.rds2.regions.return_value = [self.positive_fake_region, self.negative_fake_region]
        self.rds_snapshot = rds2.Snapshot(lambda region_name: True)

    def tearDown(self):
        patch.stopall()

    def test_fetch_unwanted_resources_filtered(self):
        self.boto_mock.rds2.connect_to_region.return_value.describe_db_snapshots.return_value = \
            self._given_db_snapshot_response()

        only_resource = list(self.rds_snapshot.fetch_unwanted_resources())[0]
        self.assertEquals(only_resource.wrapped, self.snapshot_mock)

    def test_to_string(self):
        self.boto_mock.rds2.connect_to_region.return_value.describe_db_snapshots.return_value = \
            self._given_db_snapshot_response()

        only_resource = list(self.rds_snapshot.fetch_unwanted_resources())[0]
        resource_string = self.rds_snapshot.to_string(only_resource)

        self.assertTrue(self.snapshot_mock["DBSnapshotIdentifier"] in resource_string)
        self.assertTrue(self.snapshot_mock["Status"] in resource_string)

    @patch("monocyte.handler.rds2.print", create=True)
    def test_skip_deletion_in_dry_run(self, print_mock):
        self.rds_snapshot.dry_run = True
        resource = Resource(self.snapshot_mock, self.negative_fake_region.name)

        deleted_resource = self.rds_snapshot.delete(resource)
        print_mock.assert_called_with(rds2.DRY_RUN_STATEMENT)
        self.assertEquals(None, deleted_resource)

    @patch("monocyte.handler.rds2.print", create=True)
    def test_skip_deletion_if_already_deleted(self, print_mock):
        self.rds_snapshot.dry_run = False
        self.snapshot_mock["Status"] = rds2.DELETING_STATUS

        resource = Resource(self.snapshot_mock, self.negative_fake_region.name)

        deleted_resource = self.rds_snapshot.delete(resource)
        print_mock.assert_called_with(rds2.SKIPPING_STATEMENT)
        self.assertEquals(None, deleted_resource)

    @patch("monocyte.handler.rds2.print", create=True)
    def test_skip_deletion_if_autogenerated(self, print_mock):
        self.rds_snapshot.dry_run = False
        self.snapshot_mock["SnapshotType"] = rds2.AUTOMATED_STATUS

        resource = Resource(self.snapshot_mock, self.negative_fake_region.name)

        deleted_resource = self.rds_snapshot.delete(resource)
        print_mock.assert_called_with(rds2.SKIPPING_AUTOGENERATED_STATEMENT)
        self.assertEquals(None, deleted_resource)

    def _given_db_snapshot_response(self):
        return {
            "DescribeDBSnapshotsResponse": {
                "DescribeDBSnapshotsResult": {
                    "DBSnapshots": [self.snapshot_mock]
                }
            }
        }

    def _given_snapshot_mock(self):
        return {
            "DBSnapshotIdentifier": "mySnapshotIdentifier",
            "Status": "myStatus",
            "SnapshotType": "manual"
        }