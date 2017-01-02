from __future__ import print_function, absolute_import, division
from unittest import TestCase
from mock import patch, MagicMock

import monocyte.cli as cli


class CliTest(TestCase):
    def test_cloudwatch_can_be_deactivated(self):
        test_config = {
            "cloudwatchlogs": {}
        }

        cli.apply_default_config(test_config)

        self.assertEqual(test_config["cloudwatchlogs"], {})

    def test_default_cloudwatch_config_used_when_no_cloudwatch_config_is_given(self):
        test_config = {
            "cloudwatchlogs": {"groupname": "test"}
        }

        expected_config = {
            "cloudwatchlogs": {
                'region': 'eu-central-1',
                'log_level': 20,
                'groupname': 'test'
            }
        }
        cli.apply_default_config(test_config)

        self.assertEqual(test_config["cloudwatchlogs"], expected_config["cloudwatchlogs"])

    def test_default_config_used_when_no_config_is_given(self):
        test_config = {}

        expected_config = {
            "handler_names": [
                "cloudformation.Stack",
                "ec2.Instance",
                "ec2.Volume",
                "rds2.Instance",
                "rds2.Snapshot",
                "dynamodb.Table",
                "s3.Bucket",
                "acm.Certificate"],
            "ignored_resources": {"cloudformation": ["cloudtrail-logging"]},
            "ignored_regions": ["cn-north-1", "us-gov-west-1"],
            "allowed_regions_prefixes": ["eu"]
        }
        cli.apply_default_config(test_config)

        self.assertEqual(test_config, expected_config)

    def test_default_cloudwatch_config_used_when_loglevel_is_translated(self):
        test_config = {
            "cloudwatchlogs": {
                "groupname": "test",
                "log_level": "debug"
            }
        }

        expected_config = {
            "cloudwatchlogs": {
                'region': 'eu-central-1',
                'log_level': 10,
                'groupname': 'test'
            }
        }
        cli.apply_default_config(test_config)

        self.assertEqual(test_config["cloudwatchlogs"], expected_config["cloudwatchlogs"])

    def test_region_can_be_configured(self):
        test_config = {
            "cloudwatchlogs": {"region": "my_region"}
        }

        expected_config = {
            "cloudwatchlogs": {
                'region': 'my_region',
                'log_level': 20,
                'groupname': 'monocyte_logs'
            }
        }
        cli.apply_default_config(test_config)

        self.assertEqual(test_config["cloudwatchlogs"], expected_config["cloudwatchlogs"])


class ArgumentsToConfigTest(TestCase):
    def setUp(self):
        self.whitelist = 's3://bucket/whitelist.yaml'
        self.arguments = {
            # Only an explicit 'False' may trigger deletion of resources.
            '--dry-run': 'something',
            '--config-path': '/foo/bar/batz',
            '--whitelist': self.whitelist
        }
        self.expected_config = {
            'dry_run': True
        }

    def test_get_config_path(self):
        config_path = cli.get_config_path_from_args({'--config-path':'/any/path'})
        self.assertEqual(config_path, '/any/path')

    def test_get_whitelist_from_args(self):
        whitelist = cli.get_whitelist_from_args({'--whitelist':'any_whitelist_resource'})
        self.assertEqual(whitelist, 'any_whitelist_resource')


    def test_basic_translation(self):
        config = cli.convert_arguments_to_config(self.arguments)
        self.assertEqual(config, self.expected_config)

    def test_if_no_whitelist_is_configured_None_is_returned(self):
        whitelist = cli.get_whitelist_from_args({})
        self.assertEqual(whitelist, None)

    def test_dry_run_can_be_deactivated(self):
        self.arguments['--dry-run'] = 'False'
        self.expected_config['dry_run'] = False

        config = cli.convert_arguments_to_config(self.arguments)
        self.assertEqual(config, self.expected_config)


class WhitelistLoadTest(TestCase):
    def setUp(self):
        self.expected_whitelist = {'foo':'bar'}
        self.boto3_mock = patch('monocyte.cli.boto3').start()
        self.body_mock = MagicMock()
        self.body_mock.read.return_value = "foo: bar"
        self.object_mock = MagicMock()
        self.object_mock.get.return_value = {'Body': self.body_mock}

        def side_effect(bucket_name, key):
            if bucket_name == 'any_bucket' and key == 'any_key/test':
                return self.object_mock

        self.s3_mock = MagicMock(side_effect=side_effect)
        self.s3_mock.Object.side_effect = side_effect
        self.boto3_mock.resource.return_value = self.s3_mock

    def test_load_from_s3_bucket(self):
        whitelist = cli.load_whitelist('s3://any_bucket/any_key/test')
        self.assertEqual(self.expected_whitelist, whitelist)

    def test_returns_empty_whitelist_if_uri_is_none(self):
        whitelist = cli.load_whitelist(None)
        self.assertEqual(whitelist, {})
