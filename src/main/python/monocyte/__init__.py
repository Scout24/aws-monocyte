from __future__ import print_function

from monocyte.handler import aws_handler


class Monocyte(object):

    REMOVE_WARNING = "WARNING: region '%s' not allowed, removal pending!"

    def is_region_allowed(self, region):
        return region.lower().startswith("eu")

    def is_region_ignored(self, region):
        return region.lower() in ["cn-north-1", "us-gov-west-1"]

    def is_region_handled(self, region):
        return self.is_region_allowed(region) or not self.is_region_ignored(region)

    def search_and_destroy_unwanted_resources(self):
        for handler_cls in aws_handler.all:
            print("\n---- checking %s resources" % handler_cls.SERVICE_NAME)
            handler = handler_cls(self.is_region_handled)
            for region, resource in handler.fetch_all_resources():
                if not self.is_region_allowed(region):
                    print("%s\n\t%s\n" % (
                        handler.to_string(resource, region),
                        Monocyte.REMOVE_WARNING % region))

