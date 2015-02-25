from __future__ import print_function

import boto
import boto.ec2
from boto.exception import S3ResponseError, EC2ResponseError


US_STANDARD_REGION = "us-east-1"


def make_registrar():
    registry = set()

    def registrar(cls):
        registry.add(cls)
        # print("registering aws service %s" % cls.SERVICE_NAME)
        return cls

    registrar.all = registry
    return registrar

aws_handler = make_registrar()


class Resource(object):
    def __init__(self, resource, region=None):
        self.wrapped = resource
        self.region = region


@aws_handler
class EC2(object):
    SERVICE_NAME = "ec2"

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
        if resource.wrapped.state in EC2.VALID_TARGET_STATES:
            print("\tstate '{}' is a valid target state ({}), skipping".format(
                resource.wrapped.state, ", ".join(EC2.VALID_TARGET_STATES)))
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
class S3(object):
    SERVICE_NAME = "s3"
    NR_KEYS_TO_SHOW = 4

    def __init__(self, region_filter, dry_run=True):
        self.region_filter = region_filter
        self.dry_run = dry_run

    def fetch_unwanted_resources(self):
        connection = boto.connect_s3()
        for bucket in connection.get_all_buckets():
            try:
                region = bucket.get_location()
            except S3ResponseError as e:
                # See https://github.com/boto/boto/issues/2741
                if e.status == 400:
                    print("\twarning: got an error during get_location() for %s, skipping" % bucket.name)
                    continue
                region = "__error__"
            region = region if region else US_STANDARD_REGION
            if self.region_filter(region):
                yield Resource(bucket, region)

    def to_string(self, resource):
        return "s3 bucket found in {0}\n\t{1}, created {2}".format(resource.region,
                                                                   resource.wrapped.name,
                                                                   resource.wrapped.creation_date)

    def delete(self, resource):
        if self.dry_run:
            nr_keys = len(resource.wrapped.get_all_keys())
            print("\t{} entries would be removed:".format(nr_keys))
            if nr_keys:
                for nr, key in enumerate(resource.wrapped.list()):
                    if nr >= S3.NR_KEYS_TO_SHOW:
                        print("\t... (skip remaining {} keys)".format(nr_keys - S3.NR_KEYS_TO_SHOW))
                        break
                    print("\tkey '{}'".format(key.name))
        else:
            raise NotImplementedError("really deleting s3 buckets not yet implemented")
            for key in resource.wrapped.list():
                pass

