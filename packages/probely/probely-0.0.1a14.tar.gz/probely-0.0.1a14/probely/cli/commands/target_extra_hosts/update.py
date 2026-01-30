import argparse
import logging
from typing import Dict, Iterable, Generator

from probely.cli.commands.target_extra_hosts.schemas import (
    TargetExtraHostsApiFiltersSchema,
)
from probely.cli.common import (
    validate_and_retrieve_yaml_content,
    prepare_filters_for_api,
    validate_empty_results_generator,
)
from probely.cli.renderers import render_output
from probely.cli.tables.target_extra_hosts_table import TargetExtraHostTable
from probely.exceptions import (
    ProbelyCLIValidation,
    ProbelyCLIValidationFiltersAndIDsMutuallyExclusive,
)
from probely.sdk.managers import TargetExtraHostManager
from probely.sdk.models import TargetExtraHost

logger = logging.getLogger(__name__)


def generate_payload_from_args(args: argparse.Namespace) -> Dict:
    """
    Generate payload for updating an Extra Host by prioritizing CL args
    and using file input as a fallback. Only include fields that are specified.
    """
    yaml_file_path = args.yaml_file_path
    file_content = validate_and_retrieve_yaml_content(yaml_file_path)

    payload = {}

    # Check each argument and add to payload if it is specified
    if args.include or "include" in file_content:
        payload["include"] = args.include or file_content.get("include")
    if args.name or "name" in file_content:
        payload["name"] = args.name or file_content.get("name")
    if args.description or "desc" in file_content:
        payload["desc"] = args.description or file_content.get("desc")

    # Headers and cookies could not be specified in the CL, but only in the file
    if "headers" in file_content:
        payload["headers"] = file_content["headers"]
    if "cookies" in file_content:
        payload["cookies"] = file_content["cookies"]

    return payload


def target_extra_hosts_update_command_handler(args: argparse.Namespace):
    filters = prepare_filters_for_api(TargetExtraHostsApiFiltersSchema, args)
    target_extra_hosts_ids = args.extra_hosts_ids
    is_single_record_output = len(target_extra_hosts_ids) == 1

    if not filters and not target_extra_hosts_ids:
        raise ProbelyCLIValidation(
            "either filters or Target Extra Hosts IDs must be provided."
        )

    if filters and target_extra_hosts_ids:
        raise ProbelyCLIValidationFiltersAndIDsMutuallyExclusive()

    payload = generate_payload_from_args(args)

    if filters:
        target_extra_hosts: Generator[TargetExtraHost] = TargetExtraHostManager().list(
            filters=filters
        )
        target_extra_hosts: Iterable = validate_empty_results_generator(
            target_extra_hosts
        )

    else:
        target_extra_hosts = TargetExtraHostManager().retrieve_multiple(
            target_extra_hosts_ids
        )

    updated_target_extra_hosts = []
    for target_extra_host in target_extra_hosts:
        updated_target_extra_host = TargetExtraHostManager().update(
            target_extra_host_or_id=target_extra_host,
            payload=payload,
        )
        updated_target_extra_hosts.append(updated_target_extra_host)

    render_output(
        records=updated_target_extra_hosts,
        table_cls=TargetExtraHostTable,
        args=args,
        is_single_record_output=is_single_record_output,
    )
