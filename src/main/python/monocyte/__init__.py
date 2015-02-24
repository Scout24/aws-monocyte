from __future__ import print_function

from monocyte.handler import aws_handler

REMOVE_WARNING = "WARNING: region '%s' not allowed!"
IGNORED_REGIONS = ["cn-north-1", "us-gov-west-1", "us-east-1"]
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

        registered_handlers = [handler_cls.SERVICE_NAME for handler_cls in aws_handler.all]
        print("       registered handlers: {}".format(" ".join(registered_handlers)))
        print("allowed regions start with: {}".format(ALLOWED_REGIONS_STARTS_WITH))
        print("           ignored regions: {}".format(" ".join(IGNORED_REGIONS)))

        for handler_cls in aws_handler.all:
            print("\n---- checking %s resources" % handler_cls.SERVICE_NAME)
            specific_handler = handler_cls(self.is_region_handled, dry_run)
            for resource in specific_handler.fetch_all_resources():
                if not self.is_region_allowed(resource.region):
                    print("\n%s\n\t%s" % (
                        specific_handler.to_string(resource),
                        REMOVE_WARNING % resource.region))
                    specific_handler.delete(resource)
