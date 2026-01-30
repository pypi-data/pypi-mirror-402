from probely.cli.parsers.base_parser import build_cli_parser
from probely.exceptions import (
    ProbelyCLIValidation,
    ProbelyException,
    ProbelyCLIError,
    ProbelyArgumentParserError,
    ProbelyArgumentParserExit,
)
import probely.settings as settings
from probely.sdk.client import Probely
import argparse
import logging
import sys


logger = logging.getLogger(__name__)


class CLIApp:
    args: argparse.Namespace

    def __init__(self, console, err_console, cmd_args):
        settings.IS_CLI = True

        self.base_parser = build_cli_parser()
        self.console = console
        self.err_console = err_console
        self.cmd_args = cmd_args

    def _config(self):
        args_dict = vars(self.args)
        if args_dict.get("api_key"):
            Probely.init(api_key=args_dict.get("api_key"))

    def _exit_with_error(self, message: str, cmd=None, exit_code=1) -> None:
        if not cmd:
            cmd = self.args.parser.prog

        message = "{cmd}: error: {message}".format(cmd=cmd, message=message)

        self.err_console.print(message)
        sys.exit(exit_code)

    def run(self):
        try:
            self.args = self.base_parser.parse_args(self.cmd_args)
            self.args.console = self.console
            self.args.err_console = self.err_console

            self._config()

            self.args.command_handler(self.args)
        except ProbelyArgumentParserError as e:
            usage = e.parser.format_usage().strip()
            self.err_console.print(usage)
            self._exit_with_error(str(e), cmd=e.parser.prog, exit_code=e.exit_code)
        except ProbelyArgumentParserExit as e:
            if e.message:
                self.console.print(e.message)
            sys.exit(0)
        except ProbelyCLIValidation as e:
            usage = self.args.parser.format_usage()
            self.err_console.print(usage)

            # exit_code=2 is used by argparse on validations
            self._exit_with_error(str(e), exit_code=2)
        except ProbelyCLIError as e:
            self._exit_with_error(str(e))
        except ProbelyException as e:
            self._exit_with_error(str(e))
        except KeyboardInterrupt:
            self._exit_with_error("operation was interrupted by user")
        except Exception as e:
            logger.debug(
                "Unhandled exception: {name}: {msg}".format(
                    name=type(e).__name__, msg=str(e)
                )
            )

            if settings.IS_DEBUG_MODE:
                self.args.err_console.print_exception(show_locals=True)
            else:
                self._exit_with_error(str(e))
