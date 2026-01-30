import logging
import sys
import probely.settings as settings

from rich.console import Console

from probely.cli.app import CLIApp

logger = logging.getLogger(__name__)

console = Console(
    width=sys.maxsize,  # avoids word wrapping
    force_terminal=True,
    color_system=None,
    markup=False,
)
err_console = Console(
    width=sys.maxsize,  # avoids word wrapping
    stderr=True,
    force_terminal=True,
    color_system=None,
    markup=False,
)


def app():
    cmd_args = sys.argv[1:]

    if "--debug" in cmd_args:
        settings.IS_DEBUG_MODE = True
        logging.basicConfig(level=logging.DEBUG)
        logger.debug("DEBUG MODE ON")
    else:
        logging.disabled = True

    cli_app = CLIApp(console, err_console, cmd_args)
    cli_app.run()
