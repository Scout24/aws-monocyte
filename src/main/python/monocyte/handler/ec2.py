from __future__ import print_function

import boto
import boto.ec2
from boto.exception import EC2ResponseError
from monocyte.handler import Resource, aws_handler


@aws_handler
class Instance(object):
    VALID_TARGET_STATES = ["terminated", "shutting-down"]

    def __init__(self, region_filter, dry_run=True):
        self.regions = [region for region in boto.ec2.regions() if region_filter(region.name)]
        self.dry_run = dry_run
        self.name = "ec2.instance"
        self.order = 2

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


@aws_handler
class Volume(object):
    def __init__(self, region_filter, dry_run=True):
        self.regions = [region for region in boto.ec2.regions() if region_filter(region.name)]
        self.dry_run = dry_run
        self.name = "ec2.volume"
        self.order = 3

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
        pass
