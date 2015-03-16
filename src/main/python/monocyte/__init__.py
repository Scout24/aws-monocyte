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

from cloudwatchlogs_logging import CloudWatchLogsHandler

import monocyte.handler

REMOVE_WARNING = "WARNING: region '%s' not allowed!"
IGNORED_REGIONS = ["cn-north-1", "us-gov-west-1"]
ALLOWED_REGION_PREFIXES = ["eu"]


class Monocyte(object):

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%dT%H:%M:%S')

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        self.logger.addHandler(console_handler)

        self.problematic_resources = []

    def is_region_allowed(self, region):
        region_prefix = region.lower()[:2]
        return region_prefix in ALLOWED_REGION_PREFIXES

    def is_region_ignored(self, region):
        return region.lower() in IGNORED_REGIONS

    def is_region_handled(self, region):
        return not self.is_region_allowed(region) and not self.is_region_ignored(region)

    def search_and_destroy_unwanted_resources(self, handler_names, dry_run=True):
        stream_name = "dryrun" if dry_run else "removed"

        cloudwatch_handler = CloudWatchLogsHandler("eu-central-1",
                                                   "monocyte",
                                                   stream_name,
                                                   logging.INFO)
        self.logger.addHandler(cloudwatch_handler)

        self.logger.info("Monocyte - Search and Destroy unwanted AWS Resources relentlessly.")

        if dry_run:
            self.logger.info("Dry Run Activated. Will not destroy anything.")

        handler_classes_list = [
            monocyte.handler.cloudformation.Stack,
            monocyte.handler.dynamodb.Table,
            monocyte.handler.ec2.Instance,
            monocyte.handler.ec2.Volume,
            monocyte.handler.rds2.Instance,
            monocyte.handler.rds2.Snapshot,
            monocyte.handler.s3.Bucket,
        ]
        handler_classes = {}
        for hc in handler_classes_list:
            handler_classes["%s.%s" % (hc.__module__, hc.__name__)] = hc
        specific_handlers = self.instantiate_handlers(handler_classes, handler_names, dry_run)

        self.logger.info("Handler activated in Order: {0}".format(handler_names))
        self.logger.info("Allowed regions start with: {0}".format(ALLOWED_REGION_PREFIXES))
        self.logger.info("Ignored regions: {0}".format(IGNORED_REGIONS))

        for specific_handler in specific_handlers:
            self.logger.info("Start handling %s resources" % specific_handler.name)
            self.handle_service(specific_handler)
            self.logger.info("Finish handling %s resources" % specific_handler.name)

        if self.problematic_resources:
            self.logger.info("Problems encountered while deleting the following resources.")
            for resource, service_handler, exception in self.problematic_resources:
                self.logger.warn("{0:10s} {1}: {2}".format(
                    resource.region, service_handler.name, exception))
            return 1
        return 0

    def handle_service(self, specific_handler):
        for resource in specific_handler.fetch_unwanted_resources():
            if not self.is_region_allowed(resource.region):
                self.logger.info(specific_handler.to_string(resource))
                try:
                    specific_handler.delete(resource)
                except Exception as exc:
                    self.logger.exception(exc)
                    self.problematic_resources.append((resource, specific_handler, exc))

    def instantiate_handlers(self, handler_classes, handler_names, dry_run):
        return [handler_classes["monocyte.handler." + handler_name](
                self.is_region_handled, dry_run=dry_run)
                for handler_name in handler_names]
