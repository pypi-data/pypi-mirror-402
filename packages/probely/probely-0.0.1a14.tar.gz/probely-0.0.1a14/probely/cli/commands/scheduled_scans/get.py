from typing import Generator

from probely.cli.commands.scheduled_scans.schemas import ScheduledScanApiFiltersSchema
from probely.cli.common import prepare_filters_for_api
from probely.cli.renderers import render_output
from probely.cli.tables.scheduled_scans import ScheduledScanTable
from probely.exceptions import ProbelyCLIValidationFiltersAndIDsMutuallyExclusive
from probely.sdk.managers.scheduled_scans import ScheduledScanManager
from probely.sdk.models import ScheduledScan


def scheduled_scans_get_command_handler(args):
    filters = prepare_filters_for_api(ScheduledScanApiFiltersSchema, args)
    scheduled_scans_ids = args.scheduled_scans_ids
    is_single_record_output = len(scheduled_scans_ids) == 1

    if filters and scheduled_scans_ids:
        raise ProbelyCLIValidationFiltersAndIDsMutuallyExclusive()

    if scheduled_scans_ids:
        scheduled_scans: Generator[ScheduledScan] = (
            ScheduledScanManager().retrieve_multiple(scheduled_scans_ids)
        )
    else:
        scheduled_scans: Generator[ScheduledScan] = ScheduledScanManager().list(
            filters=filters
        )

    render_output(
        records=scheduled_scans,
        table_cls=ScheduledScanTable,
        args=args,
        is_single_record_output=is_single_record_output,
    )
