from __future__ import print_function, absolute_import, division
import yamlreader
import boto3
import logging
import yaml
from monocyte import Monocyte


def read_config(path):
    return {} if path is None else yamlreader.yaml_load(path)

def get_config_path_from_args(args):
    return args["--config-path"]

def get_whitelist_from_args(args):
    return args.get('--whitelist', None)

def convert_arguments_to_config(args):
    dry_run = (args["--dry-run"] != "False")
    cli_config = {
        "dry_run": dry_run,
    }

    return cli_config


def apply_default_config(config):
    if config.get("cloudwatchlogs"):
        cloudwatchlogs_default_config = {
            'region': 'eu-central-1',
            'log_level': 'INFO',
            'groupname': 'monocyte_logs'
        }
        yamlreader.data_merge(cloudwatchlogs_default_config, config['cloudwatchlogs'])

        log_level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARN': logging.WARN,
            'ERROR': logging.ERROR
        }
        cloudwatchlogs_default_config['log_level'] = log_level_map[cloudwatchlogs_default_config['log_level'].upper()]

        config['cloudwatchlogs'] = cloudwatchlogs_default_config

    default_config = {
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
    for key in default_config.keys():
        config[key] = config.get(key, default_config[key])


def main(arguments):
    cli_config = convert_arguments_to_config(arguments)
    config_path = get_config_path_from_args(arguments)
    whitelist_uri = get_whitelist_from_args(arguments)

    config = yamlreader.data_merge(read_config(config_path), cli_config)
    config = yamlreader.data_merge(config, load_whitelist(whitelist_uri))
    apply_default_config(config)

    monocyte = Monocyte(**config)

    try:
        return monocyte.search_and_destroy_unwanted_resources()
    except Exception:
        monocyte.logger.exception("Error while running monocyte:")
        return 1


def load_whitelist(whitelist_uri):
    if whitelist_uri is not None:
        bucket_name = whitelist_uri.split('/', 4)[2]
        key = whitelist_uri.split('/', 3)[3]
        s3 = boto3.resource('s3')
        whitelist_string = s3.Object(bucket_name, key).get()['Body'].read()

        return yaml.safe_load(whitelist_string)
    return {}
