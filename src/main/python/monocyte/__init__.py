from __future__ import print_function

from monocyte.handler import aws_handler


class Monocyte(object):

    def search_and_destroy_unwanted_resources(self):
        for handler_cls in aws_handler.all:
            print("\nChecking %s resources" % handler_cls.SERVICE_NAME)
            handler = handler_cls()
            handler.fetch_all_resources()

