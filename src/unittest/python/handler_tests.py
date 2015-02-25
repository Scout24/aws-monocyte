from unittest import TestCase
from monocyte import handler
from mock import patch, Mock
import boto.ec2
import boto.s3.bucket
import boto.exception


class EC2HandlerTest(TestCase):

    def setUp(self):
        self.boto_patcher = patch("monocyte.handler.boto")
        self.boto_mock = self.boto_patcher.start()
        self.positive_fake_region = Mock(boto.ec2.regioninfo)
        self.positive_fake_region.name = "allowed_region"
        self.negative_fake_region = Mock(boto.ec2.regioninfo)
        self.negative_fake_region.name = "forbbiden_region"

        self.boto_mock.ec2.regions.return_value = [self.positive_fake_region, self.negative_fake_region]
        self.ec2_handler_filter = handler.EC2(lambda region_name: region_name == self.positive_fake_region.name)

        self.instance_mock = self._given_instance_mock()

    def tearDown(self):
        self.boto_patcher.stop()

    def test_fetch_unwanted_resources_filtered(self):
        only_resource = list(self.ec2_handler_filter.fetch_unwanted_resources())[0]
        self.assertEquals(only_resource.wrapped, self.instance_mock)

    def test_to_string(self):
        only_resource = list(self.ec2_handler_filter.fetch_unwanted_resources())[0]
        resource_string = self.ec2_handler_filter.to_string(only_resource)

        self.assertTrue(self.instance_mock.id in resource_string)
        self.assertTrue(self.instance_mock.image_id in resource_string)
        self.assertTrue(self.instance_mock.instance_type in resource_string)
        self.assertTrue(self.instance_mock.launch_time in resource_string)
        self.assertTrue(self.instance_mock.public_dns_name in resource_string)
        self.assertTrue(self.instance_mock.key_name in resource_string)
        self.assertTrue(self.instance_mock.region.name in resource_string)

    @patch("monocyte.handler.print", create=True)
    def test_delete(self, print_mock):
        resource = handler.Resource(self.instance_mock, self.negative_fake_region.name)
        connection = self.boto_mock.ec2.connect_to_region.return_value

        e = boto.exception.EC2ResponseError(412, 'boom')
        e.message = "test"
        connection.terminate_instances.side_effect = e

        deleted_resource = self.ec2_handler_filter.delete(resource)[0]
        self.assertEquals(self.instance_mock, deleted_resource)
        print_mock.assert_called_with("\tTermination test")

    def _given_instance_mock(self):
        instance_mock = Mock(boto.ec2.instance, image_id="ami-1112")
        instance_mock.id = "id-12345"
        instance_mock.instance_type = "m1.small"
        instance_mock.launch_time = "01.01.2015"
        instance_mock.public_dns_name = "test.aws.com"
        instance_mock.key_name = "test-ssh-key"
        instance_mock.region = self.positive_fake_region
        instance_mock._state = boto.ec2.instance.InstanceState(16, "running")
        instance_mock.state = instance_mock._state.name

        self.boto_mock.ec2.connect_to_region.return_value.get_only_instances.return_value = [instance_mock]
        return instance_mock


class S3HandlerTest(TestCase):

    def setUp(self):
        self.s3_handler = handler.S3(lambda region_name: True)
        self.boto_patcher = patch("monocyte.handler.boto")
        self.boto_mock = self.boto_patcher.start()
        self.bucket_mock = self._given_bucket_mock()

    def tearDown(self):
        self.boto_patcher.stop()

    def test_fetch_unwanted_resources(self):
        only_resource = list(self.s3_handler.fetch_unwanted_resources())[0]
        self.assertEquals(only_resource.wrapped, self.bucket_mock)

    @patch("monocyte.handler.print", create=True)
    def test_fetch_unwanted_resources_400_exception(self, print_mock):
        self.bucket_mock.get_location.side_effect = boto.exception.S3ResponseError(400, 'boom')
        list(self.s3_handler.fetch_unwanted_resources())

        print_mock.assert_called_with('\twarning: got an error during get_location() for test_bucket, skipping')

    def test_fetch_unwanted_resources_not_400_exception(self):
        self.bucket_mock.get_location.side_effect = boto.exception.S3ResponseError(999, 'boom')
        only_resource = list(self.s3_handler.fetch_unwanted_resources())[0]

        self.assertEquals(only_resource.region, '__error__')

    def test_fetch_unwanted_resources_set_default_region(self):
        self.bucket_mock.get_location.return_value = ""
        only_resource = list(self.s3_handler.fetch_unwanted_resources())[0]

        self.assertEquals(only_resource.region, handler.US_STANDARD_REGION)

    def test_to_string(self):
        only_resource = list(self.s3_handler.fetch_unwanted_resources())[0]
        resource_string = self.s3_handler.to_string(only_resource)

        self.assertTrue(only_resource.region in resource_string)
        self.assertTrue(self.bucket_mock.name in resource_string)
        self.assertTrue(self.bucket_mock.creation_date in resource_string)

    def _given_bucket_mock(self):
        bucket_mock = Mock(boto.s3.bucket.Bucket)
        bucket_mock.get_location.return_value = "my-stupid-region"
        bucket_mock.name = "test_bucket"
        bucket_mock.creation_date = "01.01.2015"

        self.boto_mock.connect_s3.return_value.get_all_buckets.return_value = [bucket_mock]
        return bucket_mock
