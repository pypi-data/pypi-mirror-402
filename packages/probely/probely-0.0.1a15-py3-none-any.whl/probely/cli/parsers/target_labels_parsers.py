import argparse

from probely.cli.commands.target_labels.get import target_labels_get_command_handler
from probely.cli.parsers.common import (
    ProbelyArgumentParser,
    build_configs_parser,
    build_output_parser,
    show_help,
)
from probely.cli.parsers.help_texts import (
    FILTERS_GROUP_TITLE,
    SUB_COMMAND_AVAILABLE_ACTIONS_TITLE,
    TARGET_LABELS_COMMAND_DESCRIPTION_TEXT,
    TARGET_LABELS_GET_COMMAND_DESCRIPTION_TEXT,
)


def build_target_labels_filters_parser() -> argparse.ArgumentParser:
    target_filters_parser = argparse.ArgumentParser(
        description="Filters usable in Target Label commands",
        add_help=False,
    )

    target_labels_filters_group = target_filters_parser.add_argument_group(
        title=FILTERS_GROUP_TITLE,
    )

    target_labels_filters_group.add_argument(
        "--f-search",
        metavar="SEARCH_TERM",
        help="Filter target labels by name",
        action="store",
        default=None,
    )
    return target_filters_parser


def build_target_labels_parser():
    target_label_filters_parser = build_target_labels_filters_parser()
    configs_parser = build_configs_parser()
    output_parser = build_output_parser()

    target_labels_parser = ProbelyArgumentParser(
        prog="probely target-labels",
        add_help=False,
        description=TARGET_LABELS_COMMAND_DESCRIPTION_TEXT,
    )
    target_labels_parser.set_defaults(
        command_handler=show_help,
        is_no_action_parser=True,
        parser=target_labels_parser,
    )

    target_labels_command_parser = target_labels_parser.add_subparsers(
        parser_class=ProbelyArgumentParser,
        title=SUB_COMMAND_AVAILABLE_ACTIONS_TITLE,
    )

    target_labels_get_parser = target_labels_command_parser.add_parser(
        "get",
        help=TARGET_LABELS_GET_COMMAND_DESCRIPTION_TEXT,
        parents=[configs_parser, target_label_filters_parser, output_parser],
    )
    target_labels_get_parser.add_argument(
        "target_label_ids",
        metavar="TARGET_LABEL_ID",
        nargs=argparse.ZERO_OR_MORE,
        help="Identifiers of Target Labels to list",
    )
    target_labels_get_parser.set_defaults(
        command_handler=target_labels_get_command_handler,
        parser=target_labels_get_parser,
    )

    return target_labels_parser
