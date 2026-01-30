import argparse

from probely.cli.commands.scheduled_scans.delete import (
    scheduled_scans_delete_command_handler,
)
from probely.cli.commands.scheduled_scans.get import scheduled_scans_get_command_handler
from probely.cli.commands.scheduled_scans.update import (
    scheduled_scans_update_command_handler,
)
from probely.cli.parsers.common import (
    build_configs_parser,
    ProbelyArgumentParser,
    show_help,
    build_file_parser,
    build_output_parser,
)
from probely.cli.parsers.help_texts import (
    SCHEDULED_SCANS_COMMAND_DESCRIPTION_TEXT,
    SCHEDULED_SCANS_UPDATE_COMMAND_DESCRIPTION_TEXT,
    SCHEDULED_SCANS_DELETE_COMMAND_DESCRIPTION_TEXT,
    SUB_COMMAND_AVAILABLE_ACTIONS_TITLE,
    SCHEDULED_SCANS_GET_COMMAND_DESCRIPTION_TEXT,
    FILTERS_GROUP_TITLE,
    SCHEDULED_SCANS_F_SEARCH_TEXT,
)


def build_scheduled_scans_filters_parser():
    scheduled_scans_filters_parser = ProbelyArgumentParser(
        add_help=False,  #  avoids conflicts with child's --help command
        description=SCHEDULED_SCANS_COMMAND_DESCRIPTION_TEXT,
    )

    scheduled_scans_filters_group = scheduled_scans_filters_parser.add_argument_group(
        title=FILTERS_GROUP_TITLE,
    )

    scheduled_scans_filters_group.add_argument(
        "--f-search",
        metavar="SEARCH_TERM",
        action="store",
        default=None,
        help=SCHEDULED_SCANS_F_SEARCH_TEXT,
    )

    scheduled_scans_filters_group.add_argument(
        "--f-target",
        nargs=argparse.ONE_OR_MORE,
        help="filter Scheduled Scans by list of origin targets",
        action="store",
    )

    scheduled_scans_filters_group.add_argument(
        "--f-target-label",
        metavar="TARGET_LABEL_ID",
        action="store",
        nargs=argparse.ONE_OR_MORE,
        help="Filter Scheduled Scans by Target Label identifiers",
    )

    return scheduled_scans_filters_parser


def build_scheduled_scans_parser():
    scheduled_scans_filters_parser = build_scheduled_scans_filters_parser()
    configs_parser = build_configs_parser()
    file_parser = build_file_parser()
    output_parser = build_output_parser()

    scheduled_scans_parser = ProbelyArgumentParser(
        prog="probely scheduled-scans",
        add_help=False,
        description=SCHEDULED_SCANS_COMMAND_DESCRIPTION_TEXT,
    )

    scheduled_scans_parser.set_defaults(
        command_handler=show_help,
        is_no_action_parser=True,
        parser=scheduled_scans_parser,
    )

    scheduled_scans_command_parser = scheduled_scans_parser.add_subparsers(
        parser_class=ProbelyArgumentParser,
        title=SUB_COMMAND_AVAILABLE_ACTIONS_TITLE,
    )

    scheduled_scans_get_parser = scheduled_scans_command_parser.add_parser(
        "get",
        help=SCHEDULED_SCANS_GET_COMMAND_DESCRIPTION_TEXT,
        parents=[configs_parser, output_parser, scheduled_scans_filters_parser],
    )
    scheduled_scans_get_parser.add_argument(
        "scheduled_scans_ids",
        metavar="SCHEDULED_SCAN_ID",
        nargs=argparse.ZERO_OR_MORE,
        help="Identifiers of the Schedule Scan to list",
        default=None,
    )
    scheduled_scans_get_parser.set_defaults(
        command_handler=scheduled_scans_get_command_handler,
        parser=scheduled_scans_get_parser,
    )

    scheduled_scans_update_parser = scheduled_scans_command_parser.add_parser(
        "update",
        help=SCHEDULED_SCANS_UPDATE_COMMAND_DESCRIPTION_TEXT,
        parents=[
            configs_parser,
            scheduled_scans_filters_parser,
            file_parser,
            output_parser,
        ],
    )

    scheduled_scans_update_parser.add_argument(
        "scheduled_scans_ids",
        metavar="SCHEDULED_SCAN_ID",
        nargs=argparse.ZERO_OR_MORE,
        help="Identifiers of the Scheduled Scans to update",
    )

    scheduled_scans_update_parser.set_defaults(
        command_handler=scheduled_scans_update_command_handler,
        parser=scheduled_scans_update_parser,
    )

    scheduled_scans_delete_parser = scheduled_scans_command_parser.add_parser(
        "delete",
        help=SCHEDULED_SCANS_DELETE_COMMAND_DESCRIPTION_TEXT,
        parents=[configs_parser, scheduled_scans_filters_parser],
    )
    scheduled_scans_delete_parser.add_argument(
        "scheduled_scans_ids",
        metavar="SCHEDULED_SCAN_ID",
        nargs=argparse.ZERO_OR_MORE,
        help="Identifiers of the Schedule Scans to delete",
    )
    scheduled_scans_delete_parser.set_defaults(
        command_handler=scheduled_scans_delete_command_handler,
        parser=scheduled_scans_delete_parser,
    )

    return scheduled_scans_parser
