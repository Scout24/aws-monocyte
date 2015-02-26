from __future__ import print_function

import boto
import boto.ec2
from boto.exception import EC2ResponseError
from monocyte.handler import Resource, aws_handler


@aws_handler
class Handler(object):
    VALID_TARGET_STATES = ["terminated", "shutting-down"]

    @classmethod
    def name(cls):
        return __name__.rsplit(".", 1)[1]

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
        if resource.wrapped.state in Handler.VALID_TARGET_STATES:
            print("\tstate '{}' is a valid target state ({}), skipping".format(
                resource.wrapped.state, ", ".join(Handler.VALID_TARGET_STATES)))
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
