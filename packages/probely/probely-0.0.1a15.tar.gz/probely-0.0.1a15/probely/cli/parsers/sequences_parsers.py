import argparse

from probely.cli.commands.target_sequences.delete import (
    target_sequences_delete_command_handler,
)
from probely.cli.commands.target_sequences.get import (
    target_sequences_get_command_handler,
)
from probely.cli.commands.target_sequences.update import (
    target_sequences_update_command_handler,
)
from probely.cli.parsers.common import (
    ProbelyArgumentParser,
    build_configs_parser,
    build_file_parser,
    build_output_parser,
    show_help,
)
from probely.cli.parsers.help_texts import (
    FILTERS_GROUP_TITLE,
    SEQUENCES_COMMAND_DESCRIPTION_TEXT,
    SEQUENCES_DELETE_COMMAND_DESCRIPTION_TEXT,
    SEQUENCES_GET_COMMAND_DESCRIPTION_TEXT,
    SEQUENCES_UPDATE_COMMAND_DESCRIPTION_TEXT,
    SUB_COMMAND_AVAILABLE_ACTIONS_TITLE,
)
from probely.sdk.enums import SequenceTypeEnum
from probely.settings import FALSY_VALUES, TRUTHY_VALUES


def build_sequences_filters_parser():
    sequences_filters_parser = argparse.ArgumentParser(
        description="Filters usable in Sequence commands",
        add_help=False,
    )
    target_sequences_filters_group = sequences_filters_parser.add_argument_group(
        title=FILTERS_GROUP_TITLE,
    )

    target_sequences_filters_group.add_argument(
        "--f-enabled",
        type=str.upper,
        choices=TRUTHY_VALUES + FALSY_VALUES,
        help="filter Target Sequences by enabled",
        action="store",
    )
    target_sequences_filters_group.add_argument(
        "--f-type",
        type=str.upper,
        choices=SequenceTypeEnum.cli_input_choices(),
        help="filter Target Sequences by type",
        action="store",
    )
    target_sequences_filters_group.add_argument(
        "--f-name",
        type=str,
        help="filter Target Sequences by name",
        action="store",
    )
    target_sequences_filters_group.add_argument(
        "--f-target",
        nargs=argparse.ONE_OR_MORE,
        help="filter Target Sequences by list of origin targets",
        action="store",
    )

    return sequences_filters_parser


def build_target_sequences_parser():
    sequences_filters_parser = build_sequences_filters_parser()
    configs_parser = build_configs_parser()
    file_parser = build_file_parser()
    output_parser = build_output_parser()

    sequences_parser = ProbelyArgumentParser(
        prog="probely target-sequences",
        add_help=False,
        description=SEQUENCES_COMMAND_DESCRIPTION_TEXT,
    )
    sequences_parser.set_defaults(
        command_handler=show_help,
        is_no_action_parser=True,
        parser=sequences_parser,
    )

    sequences_command_parser = sequences_parser.add_subparsers(
        parser_class=ProbelyArgumentParser,
        title=SUB_COMMAND_AVAILABLE_ACTIONS_TITLE,
    )

    sequences_get_parser = sequences_command_parser.add_parser(
        "get",
        help=SEQUENCES_GET_COMMAND_DESCRIPTION_TEXT,
        parents=[configs_parser, sequences_filters_parser, output_parser],
    )
    sequences_get_parser.add_argument(
        "sequence_ids",
        metavar="SEQUENCE_ID",
        nargs=argparse.ZERO_OR_MORE,
        help="Identifier of the sequence",
    )
    sequences_get_parser.set_defaults(
        command_handler=target_sequences_get_command_handler,
        parser=sequences_get_parser,
    )

    sequences_update_parser = sequences_command_parser.add_parser(
        "update",
        help=SEQUENCES_UPDATE_COMMAND_DESCRIPTION_TEXT,
        parents=[configs_parser, sequences_filters_parser, file_parser, output_parser],
    )

    sequences_update_parser.add_argument(
        "sequence_ids",
        metavar="SEQUENCE_ID",
        nargs=argparse.ZERO_OR_MORE,
        help="Identifiers of the Target Sequences to update",
    )

    sequences_update_parser.set_defaults(
        command_handler=target_sequences_update_command_handler,
        parser=sequences_update_parser,
    )

    sequences_delete_parser = sequences_command_parser.add_parser(
        "delete",
        help=SEQUENCES_DELETE_COMMAND_DESCRIPTION_TEXT,
        parents=[configs_parser, sequences_filters_parser],
    )

    sequences_delete_parser.add_argument(
        "sequence_ids",
        metavar="SEQUENCE_ID",
        nargs=argparse.ZERO_OR_MORE,
        help="Identifiers of the Target Sequences to delete",
    )
    sequences_delete_parser.set_defaults(
        command_handler=target_sequences_delete_command_handler,
        parser=sequences_delete_parser,
    )

    return sequences_parser
