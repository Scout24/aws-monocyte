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
from boto.exception import EC2ResponseError
from monocyte.handler import Resource, Handler


class Instance(Handler):
    VALID_TARGET_STATES = ["terminated", "shutting-down"]

    def __init__(self, region_filter, dry_run=True):
        self.regions = [region for region in boto.ec2.regions() if region_filter(region.name)]
        self.dry_run = dry_run

    def fetch_unwanted_resources(self):
        for region in self.regions:
            connection = boto.ec2.connect_to_region(region.name)
            resources = connection.get_only_instances() or []
            for resource in resources:
                yield Resource(resource, region.name)

    def to_string(self, resource):
        return "ec2 instance found in {region.name}\n\t" \
               "{id} [{image_id}] - {instance_type}, since {launch_time}" \
               "\n\tdnsname {public_dns_name}, key {key_name}, state {_state}".format(**vars(resource.wrapped))

    def delete(self, resource):
        if resource.wrapped.state in Instance.VALID_TARGET_STATES:
            print("\tstate '{}' is a valid target state ({}), skipping".format(
                resource.wrapped.state, ", ".join(Instance.VALID_TARGET_STATES)))
            return []
        connection = boto.ec2.connect_to_region(resource.region)
        if self.dry_run:
            try:
                connection.terminate_instances([resource.wrapped.id], dry_run=True)
            except EC2ResponseError as e:
                if e.status == 412:  # Precondition Failed
                    print("\tTermination {message}".format(**vars(e)))
                    return [resource.wrapped]
                raise
        else:
            instances = connection.terminate_instances([resource.wrapped.id], dry_run=False)
            print("\tInitiating shutdown sequence for {0}".format(instances))
            return instances


class Volume(Handler):
    def __init__(self, region_filter, dry_run=True):
        self.regions = [region for region in boto.ec2.regions() if region_filter(region.name)]
        self.dry_run = dry_run

    def fetch_unwanted_resources(self):
        for region in self.regions:
            connection = boto.ec2.connect_to_region(region.name)
            resources = connection.get_all_volumes() or []
            for resource in resources:
                yield Resource(resource, region.name)

    def to_string(self, resource):
        return "ebs volume found in {region.name}\n\t" \
               "{id} {status}, since {create_time}".format(**vars(resource.wrapped))

    def delete(self, resource):
        connection = boto.ec2.connect_to_region(resource.region)
        print(vars(resource.wrapped))
        if self.dry_run:
            try:
                connection.delete_volume(resource.wrapped.id, dry_run=True)
            except EC2ResponseError as e:
                if e.status == 412:  # Precondition Failed
                    print("\tTermination {message}".format(**vars(e)))
                    return [resource.wrapped]
                raise
        else:
            print("\tInitiating deletion of EBS volume {0}".format(resource.wrapped.id))
            connection.delete_volume(resource.wrapped.id, dry_run=False)
