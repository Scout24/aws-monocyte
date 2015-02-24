from unittest import TestCase
from monocyte import handler
from mock import patch, Mock
import boto.ec2
import boto.s3.bucket
import boto.exception


class EC2HandlerTest(TestCase):

    @patch("monocyte.handler.boto")
    def setUp(self, boto_mock):
        self.positive_fake_region = Mock(boto.ec2.regioninfo)
        self.positive_fake_region.name = "allowed_region"
        negative_fake_region = Mock(boto.ec2.regioninfo)
        negative_fake_region.name = "forbbiden_region"

        boto_mock.ec2.regions.return_value = [self.positive_fake_region, negative_fake_region]
        self.ec2_handler_filter = handler.EC2(lambda region_name: region_name == self.positive_fake_region.name)

    @patch("monocyte.handler.boto")
    def test_fetch_all_resources_filtered(self, boto_mock):
        instance_mock = self._given_instance_mock()
        boto_mock.ec2.connect_to_region.return_value.get_only_instances.return_value = [instance_mock]
        only_resource = list(self.ec2_handler_filter.fetch_all_resources())[0]

        self.assertEquals(only_resource.wrapped, instance_mock)

    @patch("monocyte.handler.boto")
    def test_to_string(self, boto_mock):
        instance_mock = self._given_instance_mock()
        boto_mock.ec2.connect_to_region.return_value.get_only_instances.return_value = [instance_mock]
        only_resource = list(self.ec2_handler_filter.fetch_all_resources())[0]
        resource_string = self.ec2_handler_filter.to_string(only_resource)

        self.assertTrue(instance_mock.id in resource_string)
        self.assertTrue(instance_mock.image_id in resource_string)
        self.assertTrue(instance_mock.instance_type in resource_string)
        self.assertTrue(instance_mock.launch_time in resource_string)
        self.assertTrue(instance_mock.public_dns_name in resource_string)
        self.assertTrue(instance_mock.key_name in resource_string)
        self.assertTrue(instance_mock.region.name in resource_string)

    @patch("monocyte.handler.boto")
    def test_delete(self, boto_mock):
        instance_mock = self._given_instance_mock()
        resource = handler.Resource(instance_mock, "forbidden_region")
        connection = boto_mock.ec2.connect_to_region.return_value
        connection.terminate_instances.side_effect = boto.exception.EC2ResponseError(412, 'boom')

        deleted_resource = self.ec2_handler_filter.delete(resource)[0]
        self.assertEquals(instance_mock, deleted_resource)

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
        return instance_mock


class S3HandlerTest(TestCase):

    def setUp(self):
        self.s3_handler = handler.S3()

    @patch("monocyte.handler.boto")
    def test_fetch_all_resources(self, boto_mock):
        bucket_mock = self._given_bucket_mock()
        boto_mock.connect_s3.return_value.get_all_buckets.return_value = [bucket_mock]
        only_resource = list(self.s3_handler.fetch_all_resources())[0]
        self.assertEquals(only_resource.wrapped, bucket_mock)

    @patch("monocyte.handler.boto")
    @patch("monocyte.handler.print", create=True)
    def test_fetch_all_resources_400_exception(self, print_mock, boto_mock):
        bucket_mock = self._given_bucket_mock()
        bucket_mock.get_location.side_effect = boto.exception.S3ResponseError(400, 'boom')
        boto_mock.connect_s3.return_value.get_all_buckets.return_value = [bucket_mock]
        list(self.s3_handler.fetch_all_resources())
        print_mock.assert_called_with('[WARN]  got an error during get_location() for test_bucket, skipping')

    @patch("monocyte.handler.boto")
    def test_fetch_all_resources_not_400_exception(self, boto_mock):
        bucket_mock = self._given_bucket_mock()
        bucket_mock.get_location.side_effect = boto.exception.S3ResponseError(999, 'boom')
        boto_mock.connect_s3.return_value.get_all_buckets.return_value = [bucket_mock]
        only_resource = list(self.s3_handler.fetch_all_resources())[0]

        self.assertEquals(only_resource.region, '__error__')

    @patch("monocyte.handler.boto")
    def test_fetch_all_resources_set_default_region(self, boto_mock):
        bucket_mock = self._given_bucket_mock()
        bucket_mock.get_location.return_value = ""
        boto_mock.connect_s3.return_value.get_all_buckets.return_value = [bucket_mock]
        only_resource = list(self.s3_handler.fetch_all_resources())[0]
        self.assertEquals(only_resource.region, handler.US_STANDARD_REGION)

    def _given_bucket_mock(self):
        bucket_mock = Mock(boto.s3.bucket.Bucket)
        bucket_mock.get_location.return_value = "my-stupid-region"
        bucket_mock.name = "test_bucket"
        return bucket_mock
