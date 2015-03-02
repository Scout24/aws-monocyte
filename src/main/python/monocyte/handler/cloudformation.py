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
import boto.cloudformation

from monocyte.handler import Resource, Handler, aws_handler


@aws_handler
class Handler(Handler):

    VALID_TARGET_STATES = ["DELETE_COMPLETE", "DELETE_IN_PROGRESS"]

    def __init__(self, region_filter, dry_run=True):
        self.regions = [region for region in boto.cloudformation.regions() if region_filter(region.name)]
        self.dry_run = dry_run
        self.name = "cloudformation"
        self.order = 0

    def fetch_unwanted_resources(self):
        for region in self.regions:
            connection = boto.cloudformation.connect_to_region(region.name)
            unwanted_states = set(connection.valid_states)
            unwanted_states.remove("DELETE_COMPLETE")
            resources = connection.list_stacks(stack_status_filters=list(unwanted_states)) or []
            for resource in resources:
                yield Resource(resource, region.name)

    def to_string(self, resource):
        return "CloudFormation Stack found in {region} \n\t".format(**vars(resource)) + \
               "{stack_name}, since {creation_time}" \
               "\n\tstate {stack_status}".format(**vars(resource.wrapped))

    def delete(self, resource):
        if resource.wrapped.stack_status in Handler.VALID_TARGET_STATES:
            print("\tstate '{}' is a valid target state ({}), skipping".format(
                resource.wrapped.stack_status, ", ".join(Handler.VALID_TARGET_STATES)))
            return
        if self.dry_run:
            print("\tStack would be removed")
            return
        print("\tInitiating deletion sequence")
        connection = boto.cloudformation.connect_to_region(resource.region)
        connection.delete_stack(resource.wrapped.stack_id)
