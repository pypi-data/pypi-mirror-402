import argparse
from typing import Generator, Iterable

from probely.cli.commands.scheduled_scans.schemas import ScheduledScanApiFiltersSchema

from probely.cli.common import prepare_filters_for_api, validate_empty_results_generator
from probely.exceptions import (
    ProbelyCLIValidation,
    ProbelyCLIValidationFiltersAndIDsMutuallyExclusive,
)
from probely.sdk.managers.scheduled_scans import ScheduledScanManager
from probely.sdk.models import ScheduledScan


def scheduled_scans_delete_command_handler(args: argparse.Namespace):
    filters = prepare_filters_for_api(ScheduledScanApiFiltersSchema, args)
    scheduled_scans_ids = args.scheduled_scans_ids

    if not filters and not scheduled_scans_ids:
        raise ProbelyCLIValidation(
            "either filters or Scheduled Scan IDs must be provided."
        )

    if filters and scheduled_scans_ids:
        raise ProbelyCLIValidationFiltersAndIDsMutuallyExclusive()

    if scheduled_scans_ids:
        scheduled_scans = ScheduledScanManager().retrieve_multiple(scheduled_scans_ids)
    else:
        filtered_scheduled_scans: Generator[ScheduledScan] = (
            ScheduledScanManager().list(filters=filters)
        )
        scheduled_scans: Iterable = validate_empty_results_generator(
            filtered_scheduled_scans
        )

    scheduled_scans_ids = ScheduledScanManager().bulk_delete(list(scheduled_scans))

    for scheduled_scan_id in scheduled_scans_ids:
        args.console.print(scheduled_scan_id)
