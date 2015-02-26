
from __future__ import print_function

from monocyte.handler import aws_handler


@aws_handler
class Handler(object):
    def __init__(self, region_filter, dry_run=True):
        self.region_filter = region_filter
        self.dry_run = dry_run
        self.name = __name__.rsplit(".", 1)[1]
        self.order = 1

    def fetch_unwanted_resources(self):
        return []

    def to_string(self, resource):
        pass

    def delete(self, resource):
        pass
