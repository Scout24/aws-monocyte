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
