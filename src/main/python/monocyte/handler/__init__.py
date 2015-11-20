# Monocyte - Monocyte - Search and Destroy unwanted AWS Resources relentlessly.
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

from __future__ import absolute_import
import warnings
import logging


class Resource(object):
    def __init__(self, resource, resource_type, resource_id, creation_date,
                 region=None):
        self.wrapped = resource
        self.region = region
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.creation_date = creation_date

HANDLER_PREFIX = "monocyte.handler."


class Handler(object):

    def __init__(self, region_filter, dry_run=True, logger=None, ignored_resources=None):
        warnings.filterwarnings('error')
        self.region_filter = region_filter
        self.regions = [region for region in self.fetch_regions() if self.region_filter(region.name)]
        self.dry_run = dry_run
        self.ignored_resources = ignored_resources or []
        self.logger = logger or logging.getLogger(__name__)

    @property
    def resource_type(self):
        full_type = "%s %s" % (self.__class__.__module__, self.__class__.__name__)
        return full_type.replace(HANDLER_PREFIX, "")

    @property
    def name(self):
        full_name = "%s.%s" % (self.__class__.__module__, self.__class__.__name__)
        return full_name.replace(HANDLER_PREFIX, "")

    def fetch_regions(self):
        raise NotImplementedError("Should have implemented this")

    def fetch_unwanted_resources(self):
        raise NotImplementedError("Should have implemented this")

    def to_string(self, resource):
        raise NotImplementedError("Should have implemented this")

    def delete(self, resource):
        raise NotImplementedError("Should have implemented this")
