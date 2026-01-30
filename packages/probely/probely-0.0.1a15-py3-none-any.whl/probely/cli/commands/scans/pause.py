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


def scans_pause_command_handler(args):
    filters = prepare_filters_for_api(ScanApiFiltersSchema, args)
    scan_ids = args.scan_ids
    is_single_record_output = len(scan_ids) == 1

    if not scan_ids and not filters:
        raise ProbelyCLIValidation("Expected scan_ids or filters")

    if filters and scan_ids:
        raise ProbelyCLIValidation("Filters and Scan IDs are mutually exclusive")

    if filters:
        scans: Generator[Scan] = ScanManager().list(filters=filters)
        searched_scan_ids = [scan.id for scan in scans]

        if not searched_scan_ids:
            raise ProbelyCLIFiltersNoResultsException()

        scan_ids = searched_scan_ids

    logger.debug("Pausing scan for scan ids: {}".format(scan_ids))
    if len(scan_ids) == 1:
        scan = ScanManager().pause(scan_ids[0])
        paused_scans: List[Scan] = [scan]
    else:
        paused_scans: Generator[Scan] = ScanManager().bulk_pause(scan_ids)

    render_output(
        records=paused_scans,
        table_cls=ScanTable,
        args=args,
        is_single_record_output=is_single_record_output,
    )
