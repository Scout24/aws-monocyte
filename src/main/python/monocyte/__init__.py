from __future__ import print_function

import sys

from monocyte.handler import aws_handler

REMOVE_WARNING = "WARNING: region '%s' not allowed!"
IGNORED_REGIONS = ["cn-north-1", "us-gov-west-1", "us-east-1", "us-west-2"]
ALLOWED_REGIONS_STARTS_WITH = "eu"


class Monocyte(object):

    def is_region_allowed(self, region):
        return region.lower().startswith(ALLOWED_REGIONS_STARTS_WITH)

    def is_region_ignored(self, region):
        return region.lower() in IGNORED_REGIONS

    def is_region_handled(self, region):
        return self.is_region_allowed(region) or not self.is_region_ignored(region)

    def search_and_destroy_unwanted_resources(self, dry_run=True):
        if dry_run:
            print(" DRY RUN " * 8)
            print()

        specific_handlers = [handler_cls(self.is_region_handled, dry_run) for handler_cls in aws_handler.all]
        for handler in specific_handlers:
            if not hasattr(handler, "order"):
                handler.order = sys.maxint

        specific_handlers = sorted(specific_handlers, key=lambda handler: handler.order)
        print("     order of aws handlers: {}".format(
                " -> ".join([handler.name for handler in specific_handlers])))

        print("allowed regions start with: {}".format(ALLOWED_REGIONS_STARTS_WITH))
        print("           ignored regions: {}".format(" ".join(IGNORED_REGIONS)))

        for handler in specific_handlers:
            print("\n---- checking %s resources" % handler.name)
            self.handle_service(handler)

    def handle_service(self, specific_handler):
        for resource in specific_handler.fetch_unwanted_resources():
            if not self.is_region_allowed(resource.region):
                print("\n%s\n\t%s" % (
                    specific_handler.to_string(resource),
                    REMOVE_WARNING % resource.region))
                specific_handler.delete(resource)
