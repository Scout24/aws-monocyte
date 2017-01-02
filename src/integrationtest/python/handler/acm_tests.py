import json
import logging

import boto3
import unittest2
from mock import MagicMock

from monocyte.handler import acm as acm_handler


class ACMTests(unittest2.TestCase):
    def setUp(self):
        logging.captureWarnings(True)
        self.acm_handler = acm_handler.Certificate(MagicMock, dry_run=True)

    def test_handler_finds_resources(self):
        # This test assumes that the account where it runs has at least one
        # ACM certificate (and that it cannot be valid for 10,000 days).
        acm_handler.MIN_VALID_DAYS = 10000
        resources = list(self.acm_handler.fetch_unwanted_resources())
        self.assertTrue(resources)

        # This test assumes that you do not have any certificates that expire
        # tomorrow.
        acm_handler.MIN_VALID_DAYS = 1
        resources = list(self.acm_handler.fetch_unwanted_resources())
        self.assertFalse(resources)


if __name__ == "__main__":
    unittest2.main()
