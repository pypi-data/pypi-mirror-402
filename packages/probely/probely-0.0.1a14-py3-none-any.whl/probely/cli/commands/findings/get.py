import argparse
from typing import Generator

from probely.cli.commands.findings.schemas import FindingsApiFiltersSchema
from probely.cli.common import prepare_filters_for_api
from probely.cli.renderers import render_output
from probely.cli.tables.finding_table import FindingTable
from probely.exceptions import ProbelyCLIValidation
from probely.sdk.managers import FindingManager
from probely.sdk.models import Finding


def findings_get_command_handler(args: argparse.Namespace):
    filters = prepare_filters_for_api(FindingsApiFiltersSchema, args)

    findings_ids = args.findings_ids

    if filters and args.findings_ids:
        raise ProbelyCLIValidation("filters and Finding IDs are mutually exclusive.")

    is_single_record_output = len(findings_ids) == 1

    if findings_ids:
        findings: Generator[Finding] = FindingManager().retrieve_multiple(findings_ids)
    else:
        findings: Generator[Finding] = FindingManager().list(filters=filters)

    render_output(
        records=findings,
        args=args,
        table_cls=FindingTable,
        is_single_record_output=is_single_record_output,
    )
