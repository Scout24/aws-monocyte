from unittest import TestCase
from mock import Mock, patch
from monocyte import Monocyte
from monocyte.handler import Resource


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

    @patch("monocyte.print", create=True)
    def test_handle_service(self, print_mock):
        handler = Mock()
        handler.fetch_unwanted_resources.return_value = [Resource("foo", "test_region")]
        handler.to_string.return_value = "test handler"
        self.monocyte.handle_service(handler)

        print_mock.assert_called_with("\ntest handler\n\tWARNING: region 'test_region' not allowed!")
