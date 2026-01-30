import argparse
import logging
from typing import Dict, Generator, Iterable

import marshmallow

from probely.cli.commands.targets.schemas import TargetApiFiltersSchema
from probely.cli.common import (
    validate_and_retrieve_yaml_content,
    prepare_filters_for_api,
    validate_empty_results_generator,
)
from probely.cli.renderers import render_output
from probely.cli.tables.target_extra_hosts_table import TargetExtraHostTable
from probely.exceptions import ProbelyCLIValidation
from probely.sdk.managers import TargetManager
from probely.sdk.models import TargetExtraHost, Target

logger = logging.getLogger(__name__)


def generate_payload_from_args(args: argparse.Namespace) -> Dict:
    """
    Generate payload for creating an Extra Host by prioritizing command line arguments
    and using file input as a fallback.
    """
    file_content = validate_and_retrieve_yaml_content(args.yaml_file_path)

    include_in_scan = args.include or file_content.get("include")
    bool_field = marshmallow.fields.Boolean(allow_none=True, dump_default=None)

    command_arguments = {
        "host": args.host or file_content.get("host"),
        "include": bool_field.deserialize(include_in_scan),
        "name": args.name or file_content.get("name"),
        "description": args.description or file_content.get("desc"),
        "skip_reachability_check": args.skip_reachability_check,
        "headers": file_content.get("headers"),
        "cookies": file_content.get("cookies"),
        "file_input": file_content,
    }

    return command_arguments


def add_extra_hosts_command_handler(args: argparse.Namespace):
    filters = prepare_filters_for_api(TargetApiFiltersSchema, args)
    targets_ids = args.target_ids
    is_single_record_output = len(targets_ids) == 1

    if not filters and not targets_ids:
        raise ProbelyCLIValidation("either filters or Target IDs must be provided.")

    if filters and targets_ids:
        raise ProbelyCLIValidation("filters and Target IDs are mutually exclusive.")

    payload = generate_payload_from_args(args)

    logger.debug(
        "target-extra-host `add` extra_payload: {}".format(payload["file_input"])
    )

    if payload["host"] is None:
        raise ProbelyCLIValidation("the following arguments are required: --host")

    targets: Iterable[Target] = []

    if targets_ids:
        targets: Generator[Target] = TargetManager().retrieve_multiple(targets_ids)

    if filters:
        targets_generator: Generator[Target] = TargetManager().list(filters=filters)
        targets: Iterable[Target] = validate_empty_results_generator(targets_generator)

    added_extra_hosts = []
    for target in targets:
        extra_host: TargetExtraHost = TargetManager().add_extra_host(
            target_or_id=target,
            host=payload["host"],
            include=payload["include"],
            name=payload["name"],
            description=payload["description"],
            skip_reachability_check=args.skip_reachability_check,
            headers=payload["headers"],
            cookies=payload["cookies"],
            extra_payload=payload["file_input"],
        )
        added_extra_hosts.append(extra_host)

    render_output(
        records=added_extra_hosts,
        table_cls=TargetExtraHostTable,
        args=args,
        is_single_record_output=is_single_record_output,
    )
