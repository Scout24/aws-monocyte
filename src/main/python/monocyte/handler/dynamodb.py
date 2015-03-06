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

from __future__ import print_function

import datetime

import boto
import boto.dynamodb2
import boto.dynamodb2.exceptions

from monocyte.handler import Resource, Handler


class Table(Handler):
    def fetch_regions(self):
        return boto.dynamodb2.regions()

    def fetch_unwanted_resources(self):
        for region in self.regions:
            connection = boto.dynamodb2.connect_to_region(region.name)
            names = connection.list_tables(limit=100) or {}  # TODO what happens with more than 100 tables per region?
            for name in names.get("TableNames"):
                resource = connection.describe_table(name)
                yield Resource(resource["Table"], region.name)

    def to_string(self, resource):
        table = resource.wrapped
        return "DynamoDB Table found in {0}".format(resource.region) + \
               "\n\t{0}, since {1}, state {2}".format(
                   table["TableName"],
                   datetime.datetime.fromtimestamp(table["CreationDateTime"]).strftime('%Y-%m-%d %H:%M:%S.%f'),
                   table["TableStatus"])

    def delete(self, resource):
        if self.dry_run:
            self.logger.info("\tTable would be removed")
            return
        connection = boto.dynamodb2.connect_to_region(resource.region)
        self.logger.info("\tInitiating deletion sequence")
        try:
            connection.delete_table(resource.wrapped["TableName"])
        except boto.dynamodb2.exceptions.ResourceInUseException as e:
            self.logger.info("\t{0}".format(e))
