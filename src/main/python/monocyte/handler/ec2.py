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

import warnings
from boto import ec2
from boto.exception import EC2ResponseError
from monocyte.handler import Resource, Handler


class Instance(Handler):
    VALID_TARGET_STATES = ["terminated", "shutting-down"]

    def fetch_regions(self):
        return ec2.regions()

    def fetch_unwanted_resources(self):
        for region in self.regions:
            connection = ec2.connect_to_region(region.name)
            resources = connection.get_only_instances() or []
            for resource in resources:
                resource_wrapper = Resource(resource=resource,
                                            resource_type=self.resource_type,
                                            resource_id=resource.id,
                                            creation_date=resource.launch_time,
                                            region=region.name)
                if resource.id in self.ignored_resources:
                    self.logger.info('IGNORE ' + self.to_string(resource_wrapper))
                    continue
                yield resource_wrapper

    def to_string(self, resource):
        return "ec2 instance found in {region.name}, " \
               "with identifier {id}, instance type is {instance_type}, created {launch_time}, " \
               "dnsname is {public_dns_name}, key {key_name}, with state {_state}".format(**vars(resource.wrapped))

    def delete(self, resource):
        if resource.wrapped.state in Instance.VALID_TARGET_STATES:
            raise Warning("state '{0}' is a valid target state, skipping".format(
                resource.wrapped.state))
        connection = ec2.connect_to_region(resource.region)
        if self.dry_run:
            try:
                connection.terminate_instances([resource.wrapped.id], dry_run=True)
            except EC2ResponseError as exc:
                if exc.status == 412:  # Precondition Failed
                    raise Warning("Termination {message}".format(**vars(exc)))
                raise
        else:
            instances = connection.terminate_instances([resource.wrapped.id], dry_run=False)
            self.logger.info("Initiating shutdown sequence for {0}".format(instances))
            return instances


class Volume(Handler):

    def fetch_regions(self):
        return ec2.regions()

    def fetch_unwanted_resources(self):
        for region in self.regions:
            connection = ec2.connect_to_region(region.name)
            resources = connection.get_all_volumes() or []
            for resource in resources:
                resource_wrapper = Resource(resource=resource,
                                            resource_type=self.resource_type,
                                            resource_id=resource.id,
                                            creation_date=resource.create_time,
                                            region=region.name)
                if resource.id in self.ignored_resources:
                    self.logger.info('IGNORE ' + self.to_string(resource_wrapper))
                    continue
                yield resource_wrapper

    def to_string(self, resource):
        return "ebs volume found in {region.name}, " \
               "with identifier {id}, created {create_time}, " \
               "with state {status}".format(**vars(resource.wrapped))

    def delete(self, resource):
        connection = ec2.connect_to_region(resource.region)

        if self.dry_run:
            try:
                connection.delete_volume(resource.wrapped.id, dry_run=True)
            except EC2ResponseError as exc:
                if exc.status == 412:  # Precondition Failed
                    warnings.warn(Warning("Termination {message}".format(**vars(exc))))
                raise
        else:
            self.logger.info("Initiating deletion of EBS volume {0}".format(resource.wrapped.id))
            connection.delete_volume(resource.wrapped.id, dry_run=False)
