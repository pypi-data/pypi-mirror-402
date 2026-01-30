import logging
from typing import Generator, List

from probely.cli.commands.scans.schemas import ScanApiFiltersSchema
from probely.cli.common import prepare_filters_for_api
from probely.cli.renderers import render_output
from probely.cli.tables.scan_table import ScanTable
from probely.exceptions import ProbelyCLIValidation, ProbelyCLIFiltersNoResultsException
from probely.sdk.managers import ScanManager
from probely.sdk.models import Scan

logger = logging.getLogger(__name__)


def scans_resume_command_handler(args):
    filters = prepare_filters_for_api(ScanApiFiltersSchema, args)
    scan_ids = args.scan_ids
    is_single_record_output = len(scan_ids) == 1

    if not scan_ids and not filters:
        raise ProbelyCLIValidation("Expected scan_ids or filters")

    if filters and scan_ids:
        raise ProbelyCLIValidation("Filters and Scan IDs are mutually exclusive")

    ignore_blackout_period = args.ignore_blackout_period

    if filters:
        scans: Generator[Scan] = ScanManager().list(filters=filters)
        searched_scan_ids = [scan.id for scan in scans]

        if not searched_scan_ids:
            raise ProbelyCLIFiltersNoResultsException()

        scan_ids = searched_scan_ids

    logger.debug("Resuming scan for scan ids: {}".format(scan_ids))

    if len(scan_ids) == 1:
        scan = ScanManager().resume(
            scan_ids[0], ignore_blackout_period=ignore_blackout_period
        )
        resumed_scans: List[Scan] = [scan]
    else:
        resumed_scans: Generator[Scan] = ScanManager().bulk_resume(
            scan_ids, ignore_blackout_period=ignore_blackout_period
        )

    render_output(
        records=resumed_scans,
        table_cls=ScanTable,
        args=args,
        is_single_record_output=is_single_record_output,
    )
