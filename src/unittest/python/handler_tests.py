from unittest import TestCase
from monocyte import handler
from mock import patch, Mock
import boto.ec2


class EC2_HandlerTest(TestCase):

    @patch("monocyte.handler.boto")
    def setUp(self, boto_mock):
        self.positive_fake_region = Mock(boto.ec2.regioninfo)
        self.positive_fake_region.name = "foo"
        negative_fake_region = Mock(boto.ec2.regioninfo)
        negative_fake_region.name = "bar"

        boto_mock.ec2.regions.return_value = [self.positive_fake_region, negative_fake_region]
        self.ec2_handler_filter = handler.EC2(lambda region_name: region_name == self.positive_fake_region.name)

    @patch("monocyte.handler.boto")
    def test_fetch_all_resources_filtered(self, boto_mock):
        fake_instance = Mock(boto.ec2.instance, image_id="ami-1111")
        boto_mock.ec2.connect_to_region.return_value.get_only_instances.return_value = [fake_instance]
        resources = list(self.ec2_handler_filter.fetch_all_resources())

        self.assertEquals(resources[0].wrapped, fake_instance)

    @patch("monocyte.handler.boto")
    def test_to_string(self, boto_mock):
        fake_instance = Mock(boto.ec2.instance, image_id="ami-1112")
        fake_instance.id = "id-12345"
        fake_instance.instance_type = "m1.small"
        fake_instance.launch_time = "01.01.2015"
        fake_instance.public_dns_name = "test.aws.rz.is"
        fake_instance.key_name = "test-ssh-key"
        fake_instance.region = self.positive_fake_region
        boto_mock.ec2.connect_to_region.return_value.get_only_instances.return_value = [fake_instance]
        resources = list(self.ec2_handler_filter.fetch_all_resources())
        string = self.ec2_handler_filter.to_string(resources[0])
        self.assertEquals(string, "ec2 instance found in foo\n\tid-12345 [ami-1112] - m1.small, since 01.01.2015\n\tip test.aws.rz.is, key test-ssh-key")


class S3_HandlerTest(TestCase):

    @patch("monocyte.handler.boto")
    def setUp(self, boto_mock):
        pass
