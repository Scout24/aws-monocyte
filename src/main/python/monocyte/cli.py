from __future__ import print_function, absolute_import, division
from collections import defaultdict
import yamlreader
import logging

from monocyte import Monocyte


def read_config(path):
    return {} if path is None else yamlreader.yaml_load(path)


def convert_arguments_to_config(arguments):
    dry_run = (arguments["--dry-run"] != "False")
    handlers = [handler.strip() for handler in arguments["--use-handlers"].split(",")]
    allowed_regions_prefixes = [prefix.strip() for prefix in arguments["--allowed-regions-prefixes"].split(",")]
    ignored_regions = [region.strip() for region in arguments["--ignored-regions"].split(",")]
    ignored_resources = _parse_ignored_resources(arguments["--ignored_resources"])
    config_path = arguments["--config_path"]

    config = {
        "dry_run": dry_run,
        "handlers": handlers,
        "allowed_regions_prefixes": allowed_regions_prefixes,
        "ignored_regions": ignored_regions,
        "ignored_resources": ignored_resources,
        "cloudwatchlogs": {}
    }

    cloudwatchlogs_groupname = arguments["--cwl-groupname"]
    if cloudwatchlogs_groupname:
        config["cloudwatchlogs"]["groupname"] = cloudwatchlogs_groupname

    return config_path, config


def apply_default_config(config):
    if config["cloudwatchlogs"]:
        default_config = {
            'region': 'eu-central-1',
            'log_level': 'INFO',
            'groupname': 'monocyte_logs'
        }
        yamlreader.data_merge(default_config, config['cloudwatchlogs'])

        log_level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARN': logging.WARN,
            'ERROR': logging.ERROR
        }
        default_config['log_level'] = log_level_map[default_config['log_level'].upper()]

        config['cloudwatchlogs'] = default_config


def _parse_ignored_resources(ignored_resources):
    parsed = defaultdict(list)
    for resource in ignored_resources.split(","):
        namespace, name = resource.strip().split(".")
        parsed[namespace].append(name)
    return parsed


def main(arguments):
    path, cli_config = convert_arguments_to_config(arguments)
    file_config = read_config(path)
    config = yamlreader.data_merge(file_config, cli_config)
    apply_default_config(config)

    monocyte = Monocyte(**config)

    return monocyte.search_and_destroy_unwanted_resources()
