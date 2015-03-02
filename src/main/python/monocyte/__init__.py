# Monocyte - An AWS Resource Destroyer
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

from __future__ import print_function

import monocyte.handler

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

    def search_and_destroy_unwanted_resources(self, handler_names, dry_run=True):
        if dry_run:
            print(" DRY RUN " * 8)
            print()

        handler_clss = fetch_all_handlers()
        specific_handlers = [handler_clss["monocyte.handler." + handler_name](self.is_region_handled, dry_run)
                             for handler_name in handler_names]

        print("              aws handlers: {}".format(" -> ".join(handler_names)))
        print("allowed regions start with: {}".format(ALLOWED_REGIONS_STARTS_WITH))
        print("           ignored regions: {}".format(" ".join(IGNORED_REGIONS)))

        for specific_handler in specific_handlers:
            print("\n---- checking %s resources" % specific_handler.name)
            self.handle_service(specific_handler)

    def handle_service(self, specific_handler):
        for resource in specific_handler.fetch_unwanted_resources():
            if not self.is_region_allowed(resource.region):
                print("\n%s\n\t%s" % (
                    specific_handler.to_string(resource),
                    REMOVE_WARNING % resource.region))
                specific_handler.delete(resource)


def fetch_all_handlers():
    subclasses = {}
    work = [monocyte.handler.Handler]
    while work:
        parent = work.pop()
        for child in parent.__subclasses__():
            if child not in subclasses:
                class_name = "%s.%s" % (child.__module__, child.__name__)
                subclasses[class_name] = child
                work.append(child)
    return subclasses
