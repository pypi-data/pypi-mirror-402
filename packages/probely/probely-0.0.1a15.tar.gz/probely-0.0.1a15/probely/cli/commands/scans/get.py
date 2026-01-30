import argparse
from typing import Generator

from probely.cli.commands.scans.schemas import ScanApiFiltersSchema
from probely.cli.common import prepare_filters_for_api
from probely.cli.renderers import render_output
from probely.cli.tables.scan_table import ScanTable
from probely.exceptions import ProbelyCLIValidation
from probely.sdk.managers import ScanManager
from probely.sdk.models import Scan


def scans_get_command_handler(args: argparse.Namespace):
    filters = prepare_filters_for_api(ScanApiFiltersSchema, args)
    scan_ids = args.scan_ids

    if filters and scan_ids:
        raise ProbelyCLIValidation("filters and Scan IDs are mutually exclusive.")

    is_single_record_output = len(scan_ids) == 1

    if scan_ids:
        scans: Generator[Scan] = ScanManager().retrieve_multiple(scan_ids)
    else:
        scans: Generator[Scan] = ScanManager().list(filters=filters)

    render_output(
        records=scans,
        table_cls=ScanTable,
        args=args,
        is_single_record_output=is_single_record_output,
    )
