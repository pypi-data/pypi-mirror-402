import argparse
from typing import Generator, Iterable

from probely.sdk.managers import FindingManager
from probely.sdk.models import Finding
from probely.cli.commands.findings.schemas import FindingsApiFiltersSchema
from probely.sdk.enums import SelfReviewStatusEnum
from probely.cli.common import (
    prepare_filters_for_api,
    validate_empty_results_generator,
    validate_and_retrieve_yaml_content,
)
from probely.cli.renderers import render_output
from probely.cli.tables.finding_table import FindingTable
from probely.exceptions import (
    ProbelyCLIValidation,
    ProbelyCLIValidationFiltersAndIDsMutuallyExclusive,
)


def get_command_arguments(args: argparse.Namespace):
    file_input = {}
    if args.yaml_file_path:
        file_input = validate_and_retrieve_yaml_content(args.yaml_file_path)

    command_arguments = {
        "review-status": args.review_status or file_input.get("review_status", None),
        "justification": args.justification or file_input.get("justification", None),
        "file_input": file_input,
    }

    return command_arguments


def findings_self_review_command_handler(args: argparse.Namespace):
    filters = prepare_filters_for_api(FindingsApiFiltersSchema, args)
    command_arguments = get_command_arguments(args)

    findings_ids = args.findings_ids

    if not findings_ids and not filters:
        raise ProbelyCLIValidation("expected FINDING_ID or filters")

    if not command_arguments["review-status"]:
        raise ProbelyCLIValidation("expected --review-status")

    if filters and findings_ids:
        raise ProbelyCLIValidationFiltersAndIDsMutuallyExclusive()

    if findings_ids:
        findings: Generator[Finding] = FindingManager().retrieve_multiple(findings_ids)
    else:
        findings_gen: Generator = FindingManager().list(filters=filters)
        findings: Iterable = validate_empty_results_generator(findings_gen)

    review_status_enum = SelfReviewStatusEnum[command_arguments["review-status"]]

    self_reviewed_findings = FindingManager().bulk_self_review(
        list(findings),
        review_status=review_status_enum,
        justification=command_arguments["justification"],
        extra_payload=command_arguments["file_input"],
    )

    is_single_record_output = len(findings_ids) == 1
    render_output(
        records=self_reviewed_findings,
        args=args,
        table_cls=FindingTable,
        is_single_record_output=is_single_record_output,
    )
