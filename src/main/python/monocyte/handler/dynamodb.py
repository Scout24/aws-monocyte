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

import datetime
from boto import dynamodb2
from monocyte.handler import Resource, Handler


class Table(Handler):
    def fetch_regions(self):
        return dynamodb2.regions()

    def fetch_unwanted_resources(self):
        for region in self.regions:
            connection = dynamodb2.connect_to_region(region.name)
            names = connection.list_tables(limit=100) or {}
            for name in names.get("TableNames"):
                resource = connection.describe_table(name)
                resource_wrapper = Resource(resource=resource["Table"],
                                            resource_type=self.resource_type,
                                            resource_id=resource["Table"]["TableName"],
                                            creation_date=resource["Table"]["CreationDateTime"],
                                            region=region.name)
                if name in self.ignored_resources:
                    self.logger.info('IGNORE ' + self.to_string(resource_wrapper))
                    continue

                yield resource_wrapper

    def to_string(self, resource):
        table = resource.wrapped
        return "DynamoDB Table found in {0}, ".format(resource.region) + \
               "with name {0}, created {1}, with state {2}".format(
                   table["TableName"],
                   datetime.datetime.fromtimestamp(table["CreationDateTime"]).strftime('%Y-%m-%d %H:%M:%S.%f'),
                   table["TableStatus"])

    def delete(self, resource):
        if self.dry_run:
            return
        connection = dynamodb2.connect_to_region(resource.region)
        self.logger.info("Initiating deletion sequence for {0}.".format(resource.wrapped["TableName"]))
        connection.delete_table(resource.wrapped["TableName"])
