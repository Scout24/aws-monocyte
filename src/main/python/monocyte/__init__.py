# Monocyte - Search and Destroy unwanted AWS Resources relentlessly.
# Copyright 2015 Immobilien Scout GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import monocyte.handler.cloudformation
import monocyte.handler.dynamodb
import monocyte.handler.ec2
import monocyte.handler.rds2
import monocyte.handler.s3

from cloudwatchlogs_logging import CloudWatchLogsHandler


DEFAULT_IGNORED_REGIONS = ["cn-north-1", "us-gov-west-1"]
DEFAULT_ALLOWED_REGIONS_PREFIXES = ["eu"]


class Monocyte(object):
    def __init__(self,
                 allowed_regions_prefixes=None,
                 ignored_regions=None,
                 ignored_resources=None,
                 cloudwatchlogs_groupname=None,
                 logger=None):
        if allowed_regions_prefixes:
            self.allowed_regions_prefixes = allowed_regions_prefixes
        else:
            self.allowed_regions_prefixes = DEFAULT_ALLOWED_REGIONS_PREFIXES
        self.ignored_regions = ignored_regions if ignored_regions else DEFAULT_IGNORED_REGIONS
        self.ignored_resources = ignored_resources or {}
        self.cloudwatchlogs_groupname = cloudwatchlogs_groupname

        self.logger = logger or logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%dT%H:%M:%S')

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        self.logger.addHandler(console_handler)

        self.problematic_resources = []

    def is_region_allowed(self, region):
        region_prefix = region.lower()[:2]
        return region_prefix in self.allowed_regions_prefixes

    def is_region_ignored(self, region):
        return region.lower() in self.ignored_regions

    def is_region_handled(self, region):
        return not self.is_region_allowed(region) and not self.is_region_ignored(region)

    def search_and_destroy_unwanted_resources(self, handler_names, dry_run=True):
        if self.cloudwatchlogs_groupname:
            cloudwatch_handler = CloudWatchLogsHandler("eu-central-1",
                                                       self.cloudwatchlogs_groupname,
                                                       "search_and_destroy_unwanted_resources",
                                                       logging.INFO)
            self.logger.addHandler(cloudwatch_handler)

        self.logger.warn("Monocyte - Search and Destroy unwanted AWS Resources relentlessly.")
        self.logger.info("CloudWatchLogs handler used: {0}".format(self.cloudwatchlogs_groupname))

        if dry_run:
            self.logger.info("Dry Run Activated. Will not destroy anything.")

        handler_classes = self.get_all_handler_classes()
        specific_handlers = self.instantiate_handlers(handler_classes, handler_names, dry_run)

        self.logger.info("Handler activated in Order: {0}".format(handler_names))
        self.logger.info("Allowed regions start with: {0}".format(self.allowed_regions_prefixes))
        self.logger.info("Ignored regions: {0}".format(self.ignored_regions))

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
                self.logger.warn(specific_handler.to_string(resource))
                try:
                    specific_handler.delete(resource)
                except Exception as exc:
                    self.logger.exception(exc)
                    self.problematic_resources.append((resource, specific_handler, exc))

    def instantiate_handlers(self, handler_classes, handler_names, dry_run):
        return [
            handler_classes["monocyte.handler." + handler_name](
                self.is_region_handled, dry_run=dry_run,
                ignored_resources=self.ignored_resources[handler_name.split('.')[0]]
                if handler_name.split('.')[0] in self.ignored_resources.keys() else None)
            for handler_name in handler_names]

    def get_all_handler_classes(self):
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
        return handler_classes
