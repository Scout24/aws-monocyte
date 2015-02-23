import boto
import boto.ec2
from boto.exception import S3ResponseError


US_STANDARD_REGION = "us-east-1"


def make_registrar():
    registry = set()

    def registrar(cls):
        registry.add(cls)
        print("registering aws service %s" % cls.SERVICE_NAME)
        return cls

    registrar.all = registry
    return registrar

aws_handler = make_registrar()


@aws_handler
class EC2(object):
    SERVICE_NAME = "ec2"

    def __init__(self, region_filter):
        regions = boto.ec2.regions() or []
        self.regions = [region for region in regions if region_filter(region.name)]

    def fetch_all_resources(self):
        for region in self.regions:
            connection = boto.ec2.connect_to_region(region.name)
            resources = connection.get_only_instances() or []
            for resource in resources:
                yield (region.name, resource)

    def to_string(self, resource, region=None):
        return "ec2 instance found in {region.name}\n\t{id} [{image_id}] - {instance_type}, since {launch_time}\n\tip {public_dns_name}, key {key_name}".format(**vars(resource))

    def delete(self, instance):
        pass


@aws_handler
class S3(object):
    SERVICE_NAME = "s3"

    def __init__(self, *ignored):
        pass

    def fetch_all_resources(self):
        connection = boto.connect_s3()
        for bucket in connection.get_all_buckets():
            try:
                region = bucket.get_location()
            except S3ResponseError as e:
                # See https://github.com/boto/boto/issues/2741
                if e.status == 400:
                    print("[WARN]  got an error during get_location() for %s, skipping" % bucket.name)
                    continue
                region = "__error__"
            region = region if region else US_STANDARD_REGION
            yield (region, bucket)

    def to_string(self, resource, region=None):
        return "s3 bucket found in {0}\n\t{1}, created {2}".format(region, resource.name, resource.creation_date)

    def delete(self, instance):
        pass

