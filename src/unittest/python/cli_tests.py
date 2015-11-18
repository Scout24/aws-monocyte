from __future__ import print_function, absolute_import, division
from unittest import TestCase


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
                "s3.Bucket"],
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
        self.arguments = {
            # Only an explicit 'False' may trigger deletion of resources.
            '--dry-run': "something",
            '--config-path': "/foo/bar/batz",
        }
        self.expected_config = {
            'dry_run': True
        }

    def test_basic_translation(self):
        config_path, config = cli.convert_arguments_to_config(self.arguments)

        self.assertEqual(config_path, "/foo/bar/batz")
        self.assertEqual(config, self.expected_config)

    def test_dry_run_can_be_deactivated(self):
        self.arguments['--dry-run'] = 'False'
        self.expected_config['dry_run'] = False

        _, config = cli.convert_arguments_to_config(self.arguments)
        self.assertEqual(config, self.expected_config)
