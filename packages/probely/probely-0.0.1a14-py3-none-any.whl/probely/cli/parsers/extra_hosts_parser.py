import argparse

from rich_argparse import RichHelpFormatter

from probely.cli.commands.target_extra_hosts.delete import (
    target_extra_hosts_delete_command_handler,
)
from probely.cli.commands.target_extra_hosts.get import (
    target_extra_hosts_get_command_handler,
)
from probely.cli.commands.target_extra_hosts.update import (
    target_extra_hosts_update_command_handler,
)
from probely.cli.parsers.common import (
    ProbelyArgumentParser,
    build_configs_parser,
    build_file_parser,
    build_output_parser,
    show_help,
)
from probely.cli.parsers.help_texts import (
    EXTRA_HOSTS_COMMAND_DESCRIPTION_TEXT,
    EXTRA_HOSTS_DELETE_COMMAND_DESCRIPTION_TEXT,
    EXTRA_HOSTS_GET_COMMAND_DESCRIPTION_TEXT,
    EXTRA_HOSTS_UPDATE_COMMAND_DESCRIPTION_TEXT,
    SUB_COMMAND_AVAILABLE_ACTIONS_TITLE,
    FILTERS_GROUP_TITLE,
)
from probely.settings import FALSY_VALUES, TRUTHY_VALUES


def build_target_extra_hosts_filters_parser() -> argparse.ArgumentParser:
    target_extra_hosts_filters_parser = argparse.ArgumentParser(
        description="Filters usable in Target Extra Hosts commands",
        add_help=False,
        formatter_class=RichHelpFormatter,
    )

    target_extra_hosts_filters_group = (
        target_extra_hosts_filters_parser.add_argument_group(
            title=FILTERS_GROUP_TITLE,
        )
    )

    target_extra_hosts_filters_group.add_argument(
        "--f-target",
        nargs=argparse.ONE_OR_MORE,
        help="Filter Target Extra Hosts by list of origin targets",
        action="store",
    )

    return target_extra_hosts_filters_parser


def build_target_extra_hosts_parser():
    target_extra_hosts_filters_parser = build_target_extra_hosts_filters_parser()
    configs_parser = build_configs_parser()
    file_parser = build_file_parser()
    output_parser = build_output_parser()

    extra_hosts_parser = ProbelyArgumentParser(
        prog="probely target-extra-hosts",
        add_help=False,
        description=EXTRA_HOSTS_COMMAND_DESCRIPTION_TEXT,
    )
    extra_hosts_parser.set_defaults(
        command_handler=show_help,
        is_no_action_parser=True,
        parser=extra_hosts_parser,
    )

    extra_hosts_command_parser = extra_hosts_parser.add_subparsers(
        parser_class=ProbelyArgumentParser,
        title=SUB_COMMAND_AVAILABLE_ACTIONS_TITLE,
    )

    extra_hosts_get_parser = extra_hosts_command_parser.add_parser(
        "get",
        help=EXTRA_HOSTS_GET_COMMAND_DESCRIPTION_TEXT,
        parents=[configs_parser, output_parser, target_extra_hosts_filters_parser],
    )
    extra_hosts_get_parser.add_argument(
        "extra_hosts_ids",
        metavar="EXTRA_HOST_ID",
        nargs=argparse.ZERO_OR_MORE,
        help="Identifier of the Extra Host",
    )
    extra_hosts_get_parser.set_defaults(
        command_handler=target_extra_hosts_get_command_handler,
        parser=extra_hosts_get_parser,
    )

    extra_hosts_update_parser = extra_hosts_command_parser.add_parser(
        "update",
        help=EXTRA_HOSTS_UPDATE_COMMAND_DESCRIPTION_TEXT,
        parents=[
            configs_parser,
            file_parser,
            output_parser,
            target_extra_hosts_filters_parser,
        ],
    )
    extra_hosts_update_parser.add_argument(
        "extra_hosts_ids",
        metavar="EXTRA_HOST_ID",
        nargs=argparse.ZERO_OR_MORE,
        help="Identifiers of the Extra Hosts to update",
    )
    extra_hosts_update_parser.add_argument(
        "--include",
        type=str.upper,
        choices=TRUTHY_VALUES + FALSY_VALUES,
        help="Include the extra host in the scope of the scan",
    )
    extra_hosts_update_parser.add_argument(
        "--name",
        help="Display name of the extra host",
    )
    extra_hosts_update_parser.add_argument(
        "--description",
        help="Description of the extra host",
    )
    extra_hosts_update_parser.set_defaults(
        command_handler=target_extra_hosts_update_command_handler,
        parser=extra_hosts_update_parser,
    )

    extra_hosts_delete_parser = extra_hosts_command_parser.add_parser(
        "delete",
        help=EXTRA_HOSTS_DELETE_COMMAND_DESCRIPTION_TEXT,
        parents=[configs_parser, target_extra_hosts_filters_parser],
    )
    extra_hosts_delete_parser.add_argument(
        "extra_hosts_ids",
        metavar="EXTRA_HOST_ID",
        nargs=argparse.ZERO_OR_MORE,
        help="Identifiers of the Extra Hosts to delete",
    )
    extra_hosts_delete_parser.set_defaults(
        command_handler=target_extra_hosts_delete_command_handler,
        parser=extra_hosts_delete_parser,
    )

    return extra_hosts_parser
