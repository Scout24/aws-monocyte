from __future__ import print_function, absolute_import, division
from unittest import TestCase


import monocyte.cli as cli


class CliTest(TestCase):

    def test_cloudwatch_can_be_deactivated(self):
        test_config = {
            "cloudwatchlogs": {}
            }

        expected_config = {
            "cloudwatchlogs": {}
        }
        cli.apply_default_config(test_config)

        self.assertEqual(test_config, expected_config)

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

        self.assertEqual(test_config, expected_config)
