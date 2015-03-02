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

from __future__ import print_function, absolute_import

import os


def make_registrar():
    registry = set()

    def registrar(cls):
        registry.add(cls)
        # print("registering aws service %s" % cls.SERVICE_NAME)
        return cls

    registrar.all = registry
    return registrar

aws_handler = make_registrar()


class Resource(object):
    def __init__(self, resource, region=None):
        self.wrapped = resource
        self.region = region


class Handler(object):
    def fetch_unwanted_resources(self):
        raise NotImplementedError("Should have implemented this")

    def to_string(self, resource):
        raise NotImplementedError("Should have implemented this")

    def delete(self, resource):
        raise NotImplementedError("Should have implemented this")


module = None
for module in os.listdir(os.path.dirname(__file__)):
    if module == '__init__.py' or module[-3:] != '.py':
        continue
    __import__("monocyte.handler." + module[:-3], locals(), globals())
del module
