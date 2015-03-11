# Monocyte - Search and Destroy unwanted AWS Resources relentlessly.
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


import logging

import monocyte.handler
import monocyte.loghandler

REMOVE_WARNING = "WARNING: region '%s' not allowed!"
IGNORED_REGIONS = ["cn-north-1", "us-gov-west-1", "us-east-1", "us-west-2"]
ALLOWED_REGIONS_STARTS_WITH = "eu"


class Monocyte(object):

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        console_handler = logging.StreamHandler()
        self.logger.addHandler(console_handler)

        self.problematic_resources = []

    def is_region_allowed(self, region):
        return region.lower().startswith(ALLOWED_REGIONS_STARTS_WITH)

    def is_region_ignored(self, region):
        return region.lower() in IGNORED_REGIONS

    def is_region_handled(self, region):
        return not self.is_region_allowed(region) and not self.is_region_ignored(region)

    def search_and_destroy_unwanted_resources(self, handler_names, dry_run=True):
        stream_name = "dryrun" if dry_run else "removed"

        cloudwatch_handler = monocyte.loghandler.CloudWatchHandler("eu-central-1",
                                                                   "monocyte",
                                                                   stream_name,
                                                                   logging.INFO)
        self.logger.addHandler(cloudwatch_handler)

        self.logger.info("Monocyte - Search and Destroy unwanted AWS Resources relentlessly.\n")

        if dry_run:
            self.logger.info(" DRY RUN " * 8)
            self.logger.info("\n")

        handler_classes = fetch_all_handler_classes()
        specific_handlers = self.instantiate_handlers(handler_classes, handler_names, dry_run)

        self.logger.info("              aws handlers: {0}".format(" -> ".join(handler_names)))
        self.logger.info("allowed regions start with: {0}".format(ALLOWED_REGIONS_STARTS_WITH))
        self.logger.info("           ignored regions: {0}".format(" ".join(IGNORED_REGIONS)))

        for specific_handler in specific_handlers:
            self.logger.info("\n---- checking %s resources" % specific_handler.name)
            self.handle_service(specific_handler)

        if self.problematic_resources:
            self.logger.info("\nproblems encountered while deleting the following resources:")
            for resource, service_handler, exception in self.problematic_resources:
                self.logger.info("{0:10s} {1}".format(resource.region, service_handler.name))
            return 1
        return 0

    def handle_service(self, specific_handler):
        for resource in specific_handler.fetch_unwanted_resources():
            if not self.is_region_allowed(resource.region):
                self.logger.info("\n%s\n\t%s" % (
                    specific_handler.to_string(resource),
                    REMOVE_WARNING % resource.region))
                try:
                    specific_handler.delete(resource)
                except BaseException as exc:
                    self.logger.exception("\t{0}".format(exc))
                    self.problematic_resources.append((resource, specific_handler, exc))

    def instantiate_handlers(self, handler_classes, handler_names, dry_run):
        return [handler_classes["monocyte.handler." + handler_name](
                self.is_region_handled, dry_run=dry_run)
                for handler_name in handler_names]


def fetch_all_handler_classes():
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
