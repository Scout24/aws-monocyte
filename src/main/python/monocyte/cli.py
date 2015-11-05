from __future__ import print_function, absolute_import, division
from collections import defaultdict
import yamlreader


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
    cloudwatchlogs_groupname = arguments["--cwl-groupname"]

    config = {
        "dry_run": dry_run,
        "handlers": handlers,
        "allowed_regions_prefixes": allowed_regions_prefixes,
        "ignored_regions": ignored_regions,
        "ignored_resources": ignored_resources,
        "cloudwatchlogs": {
            "groupname": cloudwatchlogs_groupname}
    }

    return config_path, config


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

    monocyte = Monocyte(config)

    return monocyte.search_and_destroy_unwanted_resources()
