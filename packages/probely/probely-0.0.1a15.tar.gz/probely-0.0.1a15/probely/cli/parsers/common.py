import argparse
from typing import Type, Optional

import rich_argparse

from probely.cli.enums import OutputEnum
from probely.exceptions import (
    ProbelyArgumentParserError,
    ProbelyArgumentParserExit,
)


def _positive_int_type(user_input: str):
    err_msg = f"{user_input} is not a positive integer"

    try:
        int_value = int(user_input)
    except ValueError:
        raise argparse.ArgumentTypeError(err_msg)

    if int_value < 0:
        raise argparse.ArgumentTypeError(err_msg)

    return int_value


def _cli_choice_type(user_choice: str):
    return user_choice.upper()


class ProbelyArgumentParser(argparse.ArgumentParser):
    def __init__(
        self,
        *args,
        formatter_class: Type[argparse.HelpFormatter] = None,
        **kwargs,
    ):
        if not formatter_class:
            formatter_class = rich_argparse.RichHelpFormatter

        super().__init__(
            *args,
            formatter_class=formatter_class,
            allow_abbrev=False,
            **kwargs,
        )

        self.register("type", "positive_int", _positive_int_type)
        self.register("type", "cli_choice", _cli_choice_type)

    def exit(self, status: int = 0, message: Optional[str] = None):
        if status != 0:
            raise ProbelyArgumentParserError(
                message,
                parser=self,
                exit_code=status,
            )

        # 'message' arg is only exists for backwards compatibility.
        # It should only exist if status != 0
        raise ProbelyArgumentParserExit(message)

    def error(self, message: str):
        raise ProbelyArgumentParserError(
            message,
            parser=self,
            exit_code=2,  # default for argparse error
        )


def show_help(args):
    if args.is_no_action_parser:
        args.parser.print_help()


def build_file_parser():
    file_parser = ProbelyArgumentParser(
        add_help=False,  #  avoids conflicts with child's --help command
        description="File allowing to send customized payload to Probely's API",
    )
    file_parser.add_argument(
        "-f",
        "--yaml-file",
        dest="yaml_file_path",
        default=None,
        help="Path to file with content to apply. Accepts same payload as listed in API docs",
    )

    return file_parser


def build_configs_parser():
    configs_parser = ProbelyArgumentParser(
        add_help=False,  #  avoids conflicts with child's --help command
        description="Configs settings parser",
    )
    configs_parser.add_argument(
        "--api-key",
        help="Authorization token to make requests to the API",
        default=None,
    )
    configs_parser.add_argument(
        "--debug",
        help="Enables debug mode setting",
        action="store_true",
        default=False,
    )
    return configs_parser


def build_output_parser():
    output_parser = ProbelyArgumentParser(
        add_help=False,  #  avoids conflicts with child's --help command
        description="Controls output format of command",
    )
    output_parser.add_argument(
        "-o",
        "--output",
        dest="output_format",
        type=str.upper,
        choices=OutputEnum.cli_input_choices(),
        help="Changes the output formats based on presets",
    )
    return output_parser
