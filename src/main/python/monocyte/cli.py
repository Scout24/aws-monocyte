from __future__ import print_function, absolute_import, division
from collections import defaultdict
import yamlreader
import logging

from monocyte import Monocyte


def read_config(path):
    return {} if path is None else yamlreader.yaml_load(path)


def convert_arguments_to_config(arguments):
    def parse_csv(csv):
        return [item.strip() for item in csv.split(',')]
    handler_names = parse_csv(arguments["--handler-names"])
    allowed_regions_prefixes = parse_csv(arguments["--allowed-regions-prefixes"])
    ignored_regions = parse_csv(arguments["--ignored-regions"])

    dry_run = (arguments["--dry-run"] != "False")
    ignored_resources = _parse_ignored_resources(arguments["--ignored-resources"])
    config_path = arguments["--config-path"]

    config = {
        "dry_run": dry_run,
        "handler_names": handler_names,
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
