import argparse

from rich_argparse import RichHelpFormatter

from probely.cli.commands.findings.get import findings_get_command_handler
from probely.cli.commands.findings.retest import findings_retest_command_handler
from probely.cli.commands.findings.self_review import (
    findings_self_review_command_handler,
)
from probely.cli.parsers.common import (
    ProbelyArgumentParser,
    build_configs_parser,
    build_output_parser,
    show_help,
    build_file_parser,
)
from probely.cli.parsers.help_texts import (
    DATETIME_F_TEXT,
    FILTERS_GROUP_TITLE,
    FINDINGS_COMMAND_DESCRIPTION_TEXT,
    FINDINGS_F_SEARCH_TEXT,
    FINDINGS_GET_COMMAND_DESCRIPTION_TEXT,
    SUB_COMMAND_AVAILABLE_ACTIONS_TITLE,
    FINDINGS_RETEST_COMMAND_DESCRIPTION_TEXT,
    FINDINGS_SELF_REVIEW_COMMAND_DESCRIPTION_TEXT,
)
from probely.constants import DATETIME_METAVAR
from probely.sdk.enums import (
    FindingSeverityEnum,
    FindingStateEnum,
    LogicalOperatorTypeEnum,
    SelfReviewStatusEnum,
)
from probely.settings import FALSY_VALUES, TRUTHY_VALUES


def build_findings_filters_parser() -> argparse.ArgumentParser:
    findings_filters_parser = argparse.ArgumentParser(
        description="Filters usable in Targets commands",
        add_help=False,
        formatter_class=RichHelpFormatter,
    )

    findings_filters_group = findings_filters_parser.add_argument_group(
        title=FILTERS_GROUP_TITLE,
    )

    findings_filters_group.add_argument(
        "--f-scans",
        nargs=argparse.ONE_OR_MORE,
        help="Filter findings by list of origin scans",
        action="store",
    )

    findings_filters_group.add_argument(
        "--f-severity",
        type=str.upper,
        nargs=argparse.ONE_OR_MORE,
        choices=FindingSeverityEnum.cli_input_choices(),
        help="Filter findings by list of severities",
        action="store",
    )

    findings_filters_group.add_argument(
        "--f-state",
        type=str.upper,
        nargs=argparse.ONE_OR_MORE,
        choices=FindingStateEnum.cli_input_choices(),
        help="Filter findings by list of states",
        action="store",
    )

    findings_filters_group.add_argument(
        "--f-target",
        nargs=argparse.ONE_OR_MORE,
        help="Filter findings by list of origin targets",
        action="store",
    )

    findings_filters_group.add_argument(
        "--f-search",
        metavar="SEARCH_TERM",
        help=FINDINGS_F_SEARCH_TEXT,
        action="store",
    )

    findings_filters_group.add_argument(
        "--f-is-new",
        type=str.upper,
        choices=TRUTHY_VALUES + FALSY_VALUES,
        help="Filter new findings",
        action="store",
    )

    findings_filters_group.add_argument(
        "--f-target-label",
        type=str,
        help="Filter findings by target label ids",
        nargs=argparse.ONE_OR_MORE,
        action="store",
    )
    findings_filters_group.add_argument(
        "--f-target-label-logical-operator",
        choices=LogicalOperatorTypeEnum.cli_input_choices(),
        type=str.upper,
        help="Logical operator to apply when filtering target labels",
        action="store",
    )

    findings_filters_group.add_argument(
        "--f-last-found-gte",
        action="store",
        metavar=DATETIME_METAVAR,
        help=DATETIME_F_TEXT.format(
            entity="findings", field="last found", detail="after, or at,"
        ),
    )
    findings_filters_group.add_argument(
        "--f-last-found-lte",
        action="store",
        metavar=DATETIME_METAVAR,
        help=DATETIME_F_TEXT.format(
            entity="findings", field="last found", detail="before, or at,"
        ),
    )

    findings_filters_group.add_argument(
        "--f-changed-gte",
        action="store",
        metavar=DATETIME_METAVAR,
        help=DATETIME_F_TEXT.format(
            entity="findings", field="changed", detail="after, or at,"
        ),
    )
    findings_filters_group.add_argument(
        "--f-changed-lte",
        action="store",
        metavar=DATETIME_METAVAR,
        help=DATETIME_F_TEXT.format(
            entity="findings", field="changed", detail="before, or at,"
        ),
    )

    return findings_filters_parser


def build_findings_parser():
    findings_filter_parser = build_findings_filters_parser()
    configs_parser = build_configs_parser()
    file_parser = build_file_parser()
    output_parser = build_output_parser()

    findings_parser = ProbelyArgumentParser(
        prog="probely findings",
        add_help=False,
        description=FINDINGS_COMMAND_DESCRIPTION_TEXT,
    )
    findings_parser.set_defaults(
        command_handler=show_help,
        is_no_action_parser=True,
        parser=findings_parser,
    )

    findings_command_parser = findings_parser.add_subparsers(
        parser_class=ProbelyArgumentParser,
        title=SUB_COMMAND_AVAILABLE_ACTIONS_TITLE,
    )

    findings_get_parser = findings_command_parser.add_parser(
        "get",
        help=FINDINGS_GET_COMMAND_DESCRIPTION_TEXT,
        parents=[configs_parser, findings_filter_parser, output_parser],
    )

    findings_get_parser.add_argument(
        "findings_ids",
        metavar="FINDING_ID",
        nargs=argparse.ZERO_OR_MORE,
        help="Identifiers of the findings to list",
    )

    findings_get_parser.set_defaults(
        command_handler=findings_get_command_handler,
        parser=findings_get_parser,
    )

    findings_retest_parser = findings_command_parser.add_parser(
        "retest",
        help=FINDINGS_RETEST_COMMAND_DESCRIPTION_TEXT,
        parents=[configs_parser, findings_filter_parser, output_parser, file_parser],
    )

    findings_retest_parser.add_argument(
        "findings_ids",
        metavar="FINDING_ID",
        nargs=argparse.ZERO_OR_MORE,
        help="Identifiers of the findings to retest",
    )

    findings_retest_parser.add_argument(
        "--ignore-blackout-period",
        help="Start Scans even if Target's in blackout period",
        action="store_true",
    )

    findings_retest_parser.add_argument(
        "--scan-profile",
        metavar="SCAN_PROFILE_ID",
        help="Scan Profile resulting Scans utilize, bypassing Target's configuration",
        action="store",
    )

    findings_retest_parser.set_defaults(
        command_handler=findings_retest_command_handler,
        parser=findings_retest_parser,
    )

    findings_self_review_parser = findings_command_parser.add_parser(
        "self-review",
        help=FINDINGS_SELF_REVIEW_COMMAND_DESCRIPTION_TEXT,
        parents=[configs_parser, findings_filter_parser, output_parser, file_parser],
    )

    findings_self_review_parser.add_argument(
        "findings_ids",
        metavar="FINDING_ID",
        nargs=argparse.ZERO_OR_MORE,
        help="Identifiers of the findings to self-review",
    )

    findings_self_review_parser.add_argument(
        "--review-status",
        type=str.upper,
        choices=SelfReviewStatusEnum.cli_input_choices(),
        help="The new review status for the finding: 'accepted' or 'rejected'.",
    )

    findings_self_review_parser.add_argument(
        "--justification",
        type=str,
        help="Justification for accepting or rejecting the finding.",
    )

    findings_self_review_parser.set_defaults(
        command_handler=findings_self_review_command_handler,
        parser=findings_self_review_parser,
    )

    return findings_parser
