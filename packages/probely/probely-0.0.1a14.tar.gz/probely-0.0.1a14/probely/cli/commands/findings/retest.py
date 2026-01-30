import argparse
from typing import Generator, Iterable

from probely import Finding, FindingManager
from probely.cli.commands.findings.schemas import FindingsApiFiltersSchema
from probely.cli.common import (
    prepare_filters_for_api,
    validate_empty_results_generator,
    validate_and_retrieve_yaml_content,
)
from probely.cli.renderers import render_output
from probely.cli.tables.finding_table import FindingTable
from probely.exceptions import ProbelyCLIValidation


def get_command_arguments(args: argparse.Namespace):
    file_input = {}
    if args.yaml_file_path:
        file_input = validate_and_retrieve_yaml_content(args.yaml_file_path)

    command_arguments = {
        "ignore_blackout_period": args.ignore_blackout_period
        or file_input.get("ignore_blackout_period", None),
        "scan_profile": args.scan_profile or file_input.get("scan_profile", None),
        "file_input": file_input,
    }

    return command_arguments


def findings_retest_command_handler(args: argparse.Namespace):
    filters = prepare_filters_for_api(FindingsApiFiltersSchema, args)
    command_arguments = get_command_arguments(args)

    findings_ids = args.findings_ids

    if not findings_ids and not filters:
        raise ProbelyCLIValidation("expected FINDING_ID or filters")

    if filters and findings_ids:
        raise ProbelyCLIValidation("filters and Finding IDs are mutually exclusive")

    if findings_ids:
        findings: Generator[Finding] = FindingManager().retrieve_multiple(findings_ids)
    else:
        findings_gen: Generator[Finding] = FindingManager().list(filters=filters)
        findings: Iterable = validate_empty_results_generator(findings_gen)

    retested_findings = FindingManager().bulk_retest(
        list(findings),
        ignore_blackout_period=command_arguments["ignore_blackout_period"],
        scan_profile=command_arguments["scan_profile"],
        extra_payload=command_arguments["file_input"],
    )

    render_output(records=retested_findings, args=args, table_cls=FindingTable)
