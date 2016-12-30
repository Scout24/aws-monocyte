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
from __future__ import print_function, absolute_import, division

import logging
import monocyte.handler.acm
import monocyte.handler.cloudformation
import monocyte.handler.dynamodb
import monocyte.handler.ec2
import monocyte.handler.rds2
import monocyte.handler.s3
import monocyte.handler.iam
from pils import get_item_from_module

from cloudwatchlogs_logging import CloudWatchLogsHandler


class Monocyte(object):
    def __init__(self,
                 allowed_regions_prefixes=None,
                 ignored_regions=None,
                 ignored_resources=None,
                 cloudwatchlogs=None,
                 handler_names=None,
                 dry_run=True,
                 logger=None,
                 whitelist=None,
                 **kwargs):
        self.allowed_regions_prefixes = allowed_regions_prefixes
        self.ignored_regions = ignored_regions
        self.ignored_resources = ignored_resources
        self.cloudwatchlogs_config = cloudwatchlogs
        self.handler_names = handler_names
        self.dry_run = dry_run
        self.whitelist = whitelist
        self.config = kwargs

        self.logger = logger or logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%dT%H:%M:%S')

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        self.logger.addHandler(console_handler)

        self.problematic_resources = []

        self.unwanted_resources = []

    def is_region_allowed(self, region):
        region_prefix = region.lower()[:2]
        return region_prefix in self.allowed_regions_prefixes

    def is_region_ignored(self, region):
        return region.lower() in self.ignored_regions

    def is_region_handled(self, region):
        return not self.is_region_allowed(region) and not self.is_region_ignored(region)

    def search_and_destroy_unwanted_resources(self):
        self.logger.warning("Monocyte - Search and Destroy unwanted AWS Resources relentlessly.")
        if self.cloudwatchlogs_config:
            cloudwatch_handler = CloudWatchLogsHandler(self.cloudwatchlogs_config["region"],
                                                       self.cloudwatchlogs_config["groupname"],
                                                       "search_and_destroy_unwanted_resources",
                                                       self.cloudwatchlogs_config["log_level"],)
            self.logger.addHandler(cloudwatch_handler)
            self.logger.info("CloudWatchLogs handler used: {0}".format(self.cloudwatchlogs_config["groupname"]))

        if self.dry_run:
            self.logger.info("Dry Run Activated. Will not destroy anything.")

        specific_handlers = self.instantiate_handlers()

        self.logger.info("Handler activated in Order: {0}".format(self.handler_names))
        self.logger.info("Allowed regions start with: {0}".format(self.allowed_regions_prefixes))
        self.logger.info("Ignored regions: {0}".format(self.ignored_regions))

        for specific_handler in specific_handlers:
            self.logger.info("Start handling %s resources" % specific_handler.name)
            try:
                self.handle_service(specific_handler)
            except Exception:
                self.logger.exception("Error while trying to fetch resources "
                                      "from %s:", specific_handler.name)
            else:
                self.logger.info("Finished handling %s resources" % specific_handler.name)

        self.start_plugins()

        if self.problematic_resources:
            self.logger.info("Problems encountered while deleting the following resources.")
            for resource, service_handler, exception in self.problematic_resources:
                self.logger.warning("{0:10s} {1}: {2}".format(
                    resource.region, service_handler.name, exception))
            return 1
        return 0

    def handle_service(self, specific_handler):
        for resource in specific_handler.fetch_unwanted_resources():
            if not self.is_region_allowed(resource.region):
                self.logger.warning(specific_handler.to_string(resource))
                try:
                    specific_handler.delete(resource)
                except Warning as warn:
                    # At least boto.ec2 throws an "exception.Warning"
                    # if dry_run would succeed.
                    self.logger.info(str(warn))
                    self.unwanted_resources.append(resource)
                except Exception as exc:
                    self.logger.error("Error while trying to delete "
                                      "resource\n%s" % str(exc))
                    self.problematic_resources.append((resource, specific_handler, exc))
                else:
                    self.unwanted_resources.append(resource)

    def instantiate_handlers(self):
        handler_classes = self.get_all_handler_classes()
        handlers = []

        for handler_name in self.handler_names:
            handler_prefix = handler_name.split('.')[0]
            ignored_resources = self.ignored_resources.get(handler_prefix)

            handler_class = handler_classes["monocyte.handler." + handler_name]
            handler = handler_class(self.is_region_handled,
                                    dry_run=self.dry_run,
                                    ignored_resources=ignored_resources,
                                    whitelist=self.whitelist)
            handlers.append(handler)

        return handlers

    def get_all_handler_classes(self):
        handler_classes_list = [
            monocyte.handler.cloudformation.Stack,
            monocyte.handler.iam.User,
            monocyte.handler.iam.InlinePolicy,
            monocyte.handler.iam.IamPolicy,
            monocyte.handler.dynamodb.Table,
            monocyte.handler.ec2.Instance,
            monocyte.handler.ec2.Volume,
            monocyte.handler.rds2.Instance,
            monocyte.handler.rds2.Snapshot,
            monocyte.handler.s3.Bucket,
            monocyte.handler.acm.Certificate,
        ]
        handler_classes = {}
        for hc in handler_classes_list:
            handler_classes["%s.%s" % (hc.__module__, hc.__name__)] = hc
        return handler_classes

    def start_plugins(self):
        for plugin in self.config.get("plugins") or []:
            module_name = plugin["module"]
            item_name = plugin["item"]
            config = plugin.get("config", {})

            self.logger.debug("Starting plugin '%s.%s' with config %s  ", module_name, item_name, config)

            PluginClass = get_item_from_module(module_name, item_name)
            plugin = PluginClass(self.unwanted_resources, self.problematic_resources, self.dry_run, **config)

            plugin.run()
            self.logger.debug("Plugin '%s.%s' finished successfully", module_name, item_name)
