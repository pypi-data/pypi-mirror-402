import argparse

from probely.cli.commands.scans.cancel import scans_cancel_command_handler
from probely.cli.commands.scans.get import scans_get_command_handler
from probely.cli.commands.scans.pause import scans_pause_command_handler
from probely.cli.commands.scans.resume import scans_resume_command_handler
from probely.cli.parsers.common import (
    ProbelyArgumentParser,
    build_configs_parser,
    build_output_parser,
    show_help,
)
from probely.cli.parsers.help_texts import (
    DATETIME_F_TEXT,
    FILTERS_GROUP_TITLE,
    SCANS_CANCEL_COMMAND_DESCRIPTION_TEXT,
    SCANS_COMMAND_DESCRIPTION_TEXT,
    SCANS_F_SEARCH_TEXT,
    SCANS_GET_COMMAND_DESCRIPTION_TEXT,
    SCANS_PAUSE_COMMAND_DESCRIPTION_TEXT,
    SCANS_RESUME_COMMAND_DESCRIPTION_TEXT,
    SUB_COMMAND_AVAILABLE_ACTIONS_TITLE,
)
from probely.constants import DATETIME_METAVAR
from probely.sdk.enums import ScanStatusEnum


def build_scan_filters_parser() -> argparse.ArgumentParser:
    scan_filters_parser = ProbelyArgumentParser(
        add_help=False,
        description=SCANS_COMMAND_DESCRIPTION_TEXT,
    )

    scan_filters_group = scan_filters_parser.add_argument_group(
        title=FILTERS_GROUP_TITLE,
    )

    scan_filters_group.add_argument(
        "--f-search",
        metavar="SEARCH_TERM",
        action="store",
        default=None,
        help=SCANS_F_SEARCH_TEXT,
    )

    scan_filters_group.add_argument(
        "--f-status",
        action="store",
        nargs=argparse.ONE_OR_MORE,
        type=str.upper,
        choices=ScanStatusEnum.cli_input_choices(),
        help="Filter by Scan status",
    )
    scan_filters_group.add_argument(
        "--f-target",
        metavar="TARGET_ID",
        action="store",
        nargs=argparse.ONE_OR_MORE,
        help="Filter scans by target IDs",
    )
    scan_filters_group.add_argument(
        "--f-target-label",
        metavar="TARGET_LABEL_ID",
        action="store",
        nargs=argparse.ONE_OR_MORE,
        help="Filter scans by target label IDs",
    )

    for date_field in ["completed", "started"]:
        for filter_lookup, description in {
            "gt": "after",
            "gte": "after, or at,",
            "lt": "before",
            "lte": "before, or at,",
        }.items():
            scan_filters_group.add_argument(
                f"--f-{date_field}-{filter_lookup}",
                action="store",
                default=None,
                metavar=DATETIME_METAVAR,
                help=DATETIME_F_TEXT.format(
                    entity="scans", field=date_field, detail=description
                ),
            )
    return scan_filters_parser


def build_scans_parser():
    scan_filters_parser = build_scan_filters_parser()

    configs_parser = build_configs_parser()
    output_parser = build_output_parser()

    scans_parser = ProbelyArgumentParser(
        prog="probely scans",
        add_help=False,
        description="Manage existing scans",
    )
    scans_parser.set_defaults(
        command_handler=show_help,
        is_no_action_parser=True,
        parser=scans_parser,
    )

    scans_command_parser = scans_parser.add_subparsers(
        parser_class=ProbelyArgumentParser,
        title=SUB_COMMAND_AVAILABLE_ACTIONS_TITLE,
    )

    scans_get_parser = scans_command_parser.add_parser(
        "get",
        help=SCANS_GET_COMMAND_DESCRIPTION_TEXT,
        parents=[configs_parser, scan_filters_parser, output_parser],
    )
    scans_get_parser.add_argument(
        "scan_ids",
        metavar="SCAN_ID",
        nargs=argparse.ZERO_OR_MORE,
        help="Identifiers of the scans to list",
    )
    scans_get_parser.set_defaults(
        command_handler=scans_get_command_handler,
        parser=scans_get_parser,
    )

    scans_pause_parser = scans_command_parser.add_parser(
        "pause",
        help=SCANS_PAUSE_COMMAND_DESCRIPTION_TEXT,
        parents=[configs_parser, scan_filters_parser, output_parser],
    )
    scans_pause_parser.add_argument(
        "scan_ids",
        metavar="SCAN_ID",
        nargs=argparse.ZERO_OR_MORE,
        help="Identifiers of the scans to pause.",
    )
    scans_pause_parser.set_defaults(
        command_handler=scans_pause_command_handler,
        parser=scans_pause_parser,
    )

    scans_cancel_parser = scans_command_parser.add_parser(
        "cancel",
        help=SCANS_CANCEL_COMMAND_DESCRIPTION_TEXT,
        parents=[configs_parser, scan_filters_parser, output_parser],
    )
    scans_cancel_parser.add_argument(
        "scan_ids",
        metavar="SCAN_ID",
        nargs=argparse.ZERO_OR_MORE,
        help="Identifiers of the scans to cancel",
    )
    scans_cancel_parser.set_defaults(
        command_handler=scans_cancel_command_handler,
        parser=scans_cancel_parser,
    )

    scans_resume_parser = scans_command_parser.add_parser(
        "resume",
        help=SCANS_RESUME_COMMAND_DESCRIPTION_TEXT,
        parents=[configs_parser, scan_filters_parser, output_parser],
    )
    scans_resume_parser.add_argument(
        "scan_ids",
        metavar="SCAN_ID",
        nargs=argparse.ZERO_OR_MORE,
        help="Identifiers of the scans to resume",
    )
    scans_resume_parser.add_argument(
        "--ignore-blackout-period",
        help="Ignore blackout period settings",
        action="store_true",
    )
    scans_resume_parser.set_defaults(
        command_handler=scans_resume_command_handler,
        parser=scans_resume_parser,
    )

    return scans_parser
