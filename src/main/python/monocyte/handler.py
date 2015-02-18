import boto
import boto.ec2
from boto.exception import S3ResponseError


US_STANDARD_REGION = "us-east-1"


def is_region_allowed(region):
    return region.lower().startswith("eu")


def is_region_ignored(region):
    return region.lower() in ["cn-north-1", "us-gov-west-1"]


def make_registrar():
    registry = {}

    def registrar(cls):
        registry[cls.SERVICE_NAME] = cls
        print("registering aws service %s" % cls.SERVICE_NAME)
        return cls

    registrar.all = registry
    return registrar

aws_handler = make_registrar()


@aws_handler
class EC2(object):
    SERVICE_NAME = "ec2"

    def __init__(self):
        regions = boto.ec2.regions() or []
        self.regions = [region for region in regions
                if not is_region_allowed(region.name) and not is_region_ignored(region.name)]

    def fetch_all_resources(self):
        for region in self.regions:
            connection = boto.ec2.connect_to_region(region.name)
            resources = self.fetch_all_resources_in_region(connection) or []
            for resource in resources:
                print("ec2 instance found in {region.name} -> MUST BE REMOVED\n\t{id} [{image_id}] - {instance_type}, since {launch_time}\n\tip {public_dns_name}, key {key_name}".format(**vars(resource)))

    def fetch_all_resources_in_region(self, connection):
        try:
            return connection.get_only_instances()
        except BaseException as e:
            print(e)
            print(connection)  # TODO more infos here

    def delete(self, instance):
        pass


@aws_handler
class S3(object):
    SERVICE_NAME = "s3"

    def fetch_all_resources(self):
        connection = boto.connect_s3()
        for bucket in connection.get_all_buckets():
            try:
                location = bucket.get_location()
            except S3ResponseError as e:
                # See https://github.com/boto/boto/issues/2741
                if e.status == 400:
                    continue
                location = "__error__"
            if not is_region_allowed(location):
                print("s3 bucket found in {0} -> {1}\n\t{2}, created {3}".format(
                    location if location else US_STANDARD_REGION,
                    "okay" if is_region_allowed(location) else "MUST BE REMOVED!",  # TODO more generic
                    bucket.name,
                    bucket.creation_date))

    def delete(self, instance):
        pass

