import argparse
import logging
from typing import Dict, Iterable, Generator

from probely.cli.commands.scheduled_scans.schemas import ScheduledScanApiFiltersSchema
from probely.cli.common import (
    validate_and_retrieve_yaml_content,
    prepare_filters_for_api,
    validate_empty_results_generator,
)
from probely.cli.renderers import render_output
from probely.cli.tables.scheduled_scans import ScheduledScanTable
from probely.exceptions import (
    ProbelyCLIValidation,
    ProbelyCLIValidationFiltersAndIDsMutuallyExclusive,
)
from probely.sdk.managers.scheduled_scans import ScheduledScanManager
from probely.sdk.models import ScheduledScan

logger = logging.getLogger(__name__)


def generate_payload_from_args(args: argparse.Namespace) -> Dict:
    """
    Generate payload for updating an Scheduled Scan by using file input.
    """
    yaml_file_path = args.yaml_file_path
    if not yaml_file_path:
        raise ProbelyCLIValidation(
            "Path to the YAML file that contains the payload is required."
        )
    payload = validate_and_retrieve_yaml_content(yaml_file_path)
    return payload


def scheduled_scans_update_command_handler(args: argparse.Namespace):
    filters = prepare_filters_for_api(ScheduledScanApiFiltersSchema, args)
    scheduled_scans_ids = args.scheduled_scans_ids
    is_single_record_output = len(scheduled_scans_ids) == 1

    if not filters and not scheduled_scans_ids:
        raise ProbelyCLIValidation(
            "either filters or Scheduled Scans IDs must be provided."
        )

    if filters and scheduled_scans_ids:
        raise ProbelyCLIValidationFiltersAndIDsMutuallyExclusive()

    payload = generate_payload_from_args(args)

    if filters:
        scheduled_scans: Generator[ScheduledScan] = ScheduledScanManager().list(
            filters=filters
        )
        scheduled_scans: Iterable = validate_empty_results_generator(scheduled_scans)

    else:
        scheduled_scans = ScheduledScanManager().retrieve_multiple(scheduled_scans_ids)

    updated_scheduled_scans = ScheduledScanManager().bulk_update(
        scheduled_scans_or_ids=scheduled_scans,
        payload=payload,
    )

    render_output(
        records=updated_scheduled_scans,
        table_cls=ScheduledScanTable,
        args=args,
        is_single_record_output=is_single_record_output,
    )
