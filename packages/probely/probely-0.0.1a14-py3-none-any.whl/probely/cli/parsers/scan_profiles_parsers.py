import argparse

from probely.cli.commands.scan_profiles.get import scan_profiles_get_command_handler
from probely.cli.parsers.common import (
    build_output_parser,
    ProbelyArgumentParser,
    show_help,
    build_configs_parser,
)
from probely.cli.parsers.help_texts import (
    SCAN_PROFILES_COMMAND_DESCRIPTION_TEXT,
    SUB_COMMAND_AVAILABLE_ACTIONS_TITLE,
    SCAN_PROFILES_GET_COMMAND_DESCRIPTION_TEXT,
    FILTERS_GROUP_TITLE,
    SCAN_PROFILES_F_SEARCH_TEXT,
)
from probely.sdk.enums import ScanProfileTargetTypeEnum
from probely.settings import TRUTHY_VALUES, FALSY_VALUES


def build_scan_profiles_filters_parser() -> argparse.ArgumentParser:
    scan_profiles_filters_parser = argparse.ArgumentParser(
        description="Filters usable in Scan Profiles commands",
        add_help=False,
    )

    scan_profiles_filters_group = scan_profiles_filters_parser.add_argument_group(
        title=FILTERS_GROUP_TITLE,
    )
    scan_profiles_filters_group.add_argument(
        "--f-is-built-in",
        type=str.upper,
        choices=TRUTHY_VALUES + FALSY_VALUES,
        help="Filter if Scan Profiles is built in or custom made by User",
        action="store",
    )
    scan_profiles_filters_group.add_argument(
        "--f-can-scan-unverified-targets",
        help="Filter Scan Profiles allowed for unverified targets",
        action="store_true",
    )
    scan_profiles_filters_group.add_argument(
        "--f-type",
        type=str.upper,
        choices=ScanProfileTargetTypeEnum.cli_input_choices(),
        help="Filter Scan Profiles by type",
        action="store",
    )
    scan_profiles_filters_group.add_argument(
        "--f-is-archived",
        type=str.upper,
        choices=TRUTHY_VALUES + FALSY_VALUES,
        help="Filter if Scan Profiles are or not archived",
        action="store",
    )

    scan_profiles_filters_group.add_argument(
        "--f-search",
        metavar="SEARCH_TERM",
        help=SCAN_PROFILES_F_SEARCH_TEXT,
        action="store",
    )

    return scan_profiles_filters_parser


def build_scan_profiles_parser():
    scan_profiles_filters_parser = build_scan_profiles_filters_parser()
    configs_parser = build_configs_parser()
    output_parser = build_output_parser()

    scan_profiles_parser = ProbelyArgumentParser(
        prog="probely scan-profiles",
        add_help=False,
        description=SCAN_PROFILES_COMMAND_DESCRIPTION_TEXT,
    )

    scan_profiles_parser.set_defaults(
        command_handler=show_help,
        is_no_action_parser=True,
        parser=scan_profiles_parser,
    )

    scan_profiles_command_parser = scan_profiles_parser.add_subparsers(
        parser_class=ProbelyArgumentParser,
        title=SUB_COMMAND_AVAILABLE_ACTIONS_TITLE,
    )

    scan_profile_get_parser = scan_profiles_command_parser.add_parser(
        "get",
        help=SCAN_PROFILES_GET_COMMAND_DESCRIPTION_TEXT,
        parents=[configs_parser, output_parser, scan_profiles_filters_parser],
    )
    scan_profile_get_parser.add_argument(
        "scan_profile_ids",
        metavar="SCAN_PROFILE_ID",
        nargs=argparse.ZERO_OR_MORE,
        help="Identifiers of the Scan Profiles to list",
    )
    scan_profile_get_parser.set_defaults(
        command_handler=scan_profiles_get_command_handler,
        parser=scan_profile_get_parser,
    )

    return scan_profiles_parser
