from probely.cli.parsers.common import ProbelyArgumentParser, show_help
from probely.cli.parsers.extra_hosts_parser import build_target_extra_hosts_parser
from probely.cli.parsers.findings_parsers import build_findings_parser
from probely.cli.parsers.help_texts import (
    EXTRA_HOSTS_COMMAND_DESCRIPTION_TEXT,
    FINDINGS_COMMAND_DESCRIPTION_TEXT,
    SCANS_COMMAND_DESCRIPTION_TEXT,
    SEQUENCES_COMMAND_DESCRIPTION_TEXT,
    TARGET_COMMAND_DESCRIPTION_TEXT,
    TARGET_LABELS_COMMAND_DESCRIPTION_TEXT,
    SCAN_PROFILES_COMMAND_DESCRIPTION_TEXT,
    SCHEDULED_SCANS_COMMAND_DESCRIPTION_TEXT,
)
from probely.cli.parsers.scan_profiles_parsers import build_scan_profiles_parser
from probely.cli.parsers.scans_parsers import build_scans_parser
from probely.cli.parsers.scheduled_scans_parsers import build_scheduled_scans_parser
from probely.cli.parsers.sequences_parsers import build_target_sequences_parser
from probely.cli.parsers.target_labels_parsers import build_target_labels_parser
from probely.cli.parsers.targets_parsers import build_targets_parser
from probely.version import __version__


def build_cli_parser():
    targets_subcommand_parser = build_targets_parser()
    target_labels_subcommand_parser = build_target_labels_parser()
    target_sequences_subcommand_parser = build_target_sequences_parser()
    target_extra_hosts_subcommand_parser = build_target_extra_hosts_parser()
    # target_settings_subcommand_parser = build_target_settings_parser()
    scans_subcommand_parser = build_scans_parser()
    findings_subcommand_parser = build_findings_parser()
    scan_profiles_subcommand_parser = build_scan_profiles_parser()
    scheduled_scans_subcommand_parser = build_scheduled_scans_parser()

    probely_parser = ProbelyArgumentParser(
        prog="probely",
        description="Probely's CLI. Check subcommands for available actions",
    )
    probely_parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {__version__}"
    )

    probely_parser.set_defaults(
        command_handler=show_help,
        is_no_action_parser=True,
        parser=probely_parser,
    )

    subcommands_parser = probely_parser.add_subparsers(
        parser_class=ProbelyArgumentParser,
        title="Subcommands for available contexts",
    )

    subcommands_parser.add_parser(
        name="targets",
        parents=[targets_subcommand_parser],
        help=TARGET_COMMAND_DESCRIPTION_TEXT,
    )
    subcommands_parser.add_parser(
        name="scans",
        parents=[scans_subcommand_parser],
        help=SCANS_COMMAND_DESCRIPTION_TEXT,
    )
    subcommands_parser.add_parser(
        name="findings",
        parents=[findings_subcommand_parser],
        help=FINDINGS_COMMAND_DESCRIPTION_TEXT,
    )

    subcommands_parser.add_parser(
        name="scan-profiles",
        parents=[scan_profiles_subcommand_parser],
        help=SCAN_PROFILES_COMMAND_DESCRIPTION_TEXT,
    )

    subcommands_parser.add_parser(
        name="target-labels",
        parents=[target_labels_subcommand_parser],
        help=TARGET_LABELS_COMMAND_DESCRIPTION_TEXT,
    )

    subcommands_parser.add_parser(
        name="target-sequences",
        parents=[target_sequences_subcommand_parser],
        help=SEQUENCES_COMMAND_DESCRIPTION_TEXT,
    )

    subcommands_parser.add_parser(
        name="target-extra-hosts",
        parents=[target_extra_hosts_subcommand_parser],
        help=EXTRA_HOSTS_COMMAND_DESCRIPTION_TEXT,
    )

    subcommands_parser.add_parser(
        name="scheduled-scans",
        parents=[scheduled_scans_subcommand_parser],
        help=SCHEDULED_SCANS_COMMAND_DESCRIPTION_TEXT,
    )

    # subcommands_parser.add_parser(
    #     name="target-settings",
    #     parents=[target_settings_subcommand_parser],
    #     help=TARGET_SETTINGS_COMMAND_DESCRIPTION_TEXT,
    # )

    return probely_parser
