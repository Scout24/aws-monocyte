from unittest import TestCase
from monocyte import Monocyte


class MonocyteTest(TestCase):

    def setUp(self):
        self.monocyte = Monocyte()
        self.allowed_region = "EU"
        self.not_allowed_region = "US"
        self.ignored_region = "us-gov-west-1"

    def test_is_region_allowed(self):

        self.assertTrue(self.monocyte.is_region_allowed(self.allowed_region))
        self.assertFalse(self.monocyte.is_region_allowed(self.not_allowed_region))

    def test_is_region_ignored(self):

        self.assertTrue(self.monocyte.is_region_ignored(self.ignored_region))
        self.assertFalse(self.monocyte.is_region_ignored(self.allowed_region))

    def test_is_region_handled(self):

        self.assertTrue(self.monocyte.is_region_handled(self.allowed_region))
        self.assertFalse(self.monocyte.is_region_handled(self.ignored_region))
