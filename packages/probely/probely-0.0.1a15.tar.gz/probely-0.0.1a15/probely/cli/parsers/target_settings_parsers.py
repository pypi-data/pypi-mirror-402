from probely.cli.commands.target_settings.add import target_settings_add_command_handler
from probely.cli.commands.target_settings.export import (
    target_settings_export_command_handler,
)
from probely.cli.commands.target_settings.update import (
    target_settings_update_command_handler,
)
from probely.cli.parsers.common import ProbelyArgumentParser, show_help
from probely.cli.parsers.help_texts import (
    SUB_COMMAND_AVAILABLE_ACTIONS_TITLE,
    TARGET_SETTINGS_COMMAND_DESCRIPTION_TEXT,
    TARGET_SETTINGS_ADD_COMMAND_DESCRIPTION_TEXT,
    TARGET_SETTINGS_UPDATE_COMMAND_DESCRIPTION_TEXT,
    TARGET_SETTINGS_EXPORT_COMMAND_DESCRIPTION_TEXT,
)


def build_target_settings_parser():
    target_settings_parser = ProbelyArgumentParser(
        prog="probely target-settings",
        add_help=False,
        description=TARGET_SETTINGS_COMMAND_DESCRIPTION_TEXT,
    )
    target_settings_parser.set_defaults(
        command_handler=show_help,
        is_no_action_parser=True,
        parser=target_settings_parser,
    )

    target_settings_command_parser = target_settings_parser.add_subparsers(
        parser_class=ProbelyArgumentParser,
        title=SUB_COMMAND_AVAILABLE_ACTIONS_TITLE,
    )

    target_settings_export_parser = target_settings_command_parser.add_parser(
        "export",
        help=TARGET_SETTINGS_EXPORT_COMMAND_DESCRIPTION_TEXT,
    )
    target_settings_export_parser.add_argument(
        "target_id",
        metavar="TARGET_ID",
        help="Identifier of Target to export settings files",
    )
    target_settings_export_parser.set_defaults(
        command_handler=target_settings_export_command_handler,
        parser=target_settings_export_parser,
    )

    target_settings_update_parser = target_settings_command_parser.add_parser(
        "update",
        help=TARGET_SETTINGS_UPDATE_COMMAND_DESCRIPTION_TEXT,
    )
    target_settings_update_parser.add_argument(
        "target_ids",
        metavar="TARGET_ID",
        help="Identifiers of Targets to update settings",
    )
    target_settings_update_parser.set_defaults(
        command_handler=target_settings_update_command_handler,
        parser=target_settings_update_parser,
    )

    target_settings_add_parser = target_settings_command_parser.add_parser(
        "add",
        help=TARGET_SETTINGS_ADD_COMMAND_DESCRIPTION_TEXT,
    )
    target_settings_add_parser.set_defaults(
        command_handler=target_settings_add_command_handler,
        parser=target_settings_add_parser,
    )

    return target_settings_parser
