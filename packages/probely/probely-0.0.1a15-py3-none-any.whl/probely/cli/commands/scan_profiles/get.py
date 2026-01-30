import argparse
from typing import Generator, List

from probely.cli.commands.scan_profiles.schemas import ScanProfileApiFiltersSchema
from probely.cli.common import prepare_filters_for_api
from probely.cli.renderers import render_output
from probely.cli.tables.scan_profiles import ScanProfileTable
from probely.exceptions import ProbelyCLIValidation
from probely.sdk.managers.scan_profiles import ScanProfileManager
from probely.sdk.models import ScanProfile


def scan_profiles_get_command_handler(args: argparse.Namespace):
    filters = prepare_filters_for_api(ScanProfileApiFiltersSchema, args)
    scan_profile_ids = args.scan_profile_ids

    if filters and scan_profile_ids:
        raise ProbelyCLIValidation(
            "filters and Scan Profile IDs are mutually exclusive."
        )

    is_single_record_output = len(scan_profile_ids) == 1

    if scan_profile_ids:
        scan_profiles: List[ScanProfile] = ScanProfileManager().retrieve_multiple(
            scan_profile_ids
        )
    else:
        scan_profiles: Generator[ScanProfile] = ScanProfileManager().list(
            filters=filters
        )

    render_output(
        records=scan_profiles,
        table_cls=ScanProfileTable,
        args=args,
        is_single_record_output=is_single_record_output,
    )
