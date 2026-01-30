import argparse
import datetime

from probely.cli.commands.targets.add import targets_add_command_handler
from probely.cli.commands.targets.add_extra_host import add_extra_hosts_command_handler
from probely.cli.commands.targets.add_sequence import add_sequence_command_handler
from probely.cli.commands.targets.delete import targets_delete_command_handler
from probely.cli.commands.targets.follow_scan import targets_follow_scan_command_handler
from probely.cli.commands.targets.get import targets_get_command_handler
from probely.cli.commands.targets.schedule_scan import (
    targets_schedule_scan_command_handler,
)
from probely.cli.commands.targets.start_scan import targets_start_scan_command_handler
from probely.cli.commands.targets.update import targets_update_command_handler
from probely.cli.parsers.common import (
    ProbelyArgumentParser,
    build_configs_parser,
    build_file_parser,
    build_output_parser,
    show_help,
)
from probely.cli.parsers.help_texts import (
    FILTERS_GROUP_TITLE,
    TARGETS_ADD_SEQUENCE_COMMAND_DESCRIPTION_TEXT,
    SUB_COMMAND_AVAILABLE_ACTIONS_TITLE,
    TARGET_COMMAND_DESCRIPTION_TEXT,
    TARGETS_ADD_COMMAND_DESCRIPTION_TEXT,
    TARGETS_DELETE_COMMAND_DESCRIPTION_TEXT,
    TARGETS_F_SEARCH_TEXT,
    TARGETS_GET_COMMAND_DESCRIPTION_TEXT,
    TARGETS_START_SCAN_COMMAND_DESCRIPTION_TEXT,
    TARGETS_UPDATE_COMMAND_DESCRIPTION_TEXT,
    TARGETS_ADD_EXTRA_HOST_COMMAND_DESCRIPTION_TEXT,
    TARGETS_FOLLOW_SCAN_COMMAND_DESCRIPTION_TEXT,
    TARGETS_SCHEDULE_SCAN_COMMAND_DESCRIPTION_TEXT,
)
from probely.constants import DATETIME_METAVAR
from probely.sdk.enums import (
    LogicalOperatorTypeEnum,
    SequenceTypeEnum,
    TargetAPISchemaTypeEnum,
    TargetRiskEnum,
    TargetTypeEnum,
    ScheduledScanRecurrenceEnum,
    ScheduledScanDayOfWeekEnum,
    ScheduledScanWeekOfMonthEnum,
    FindingSeverityEnum,
)
from probely.settings import FALSY_VALUES, TRUTHY_VALUES


def build_targets_filters_parser() -> argparse.ArgumentParser:
    target_filters_parser = argparse.ArgumentParser(
        description="Filters usable in Targets commands",
        add_help=False,
    )

    target_filters_group = target_filters_parser.add_argument_group(
        title=FILTERS_GROUP_TITLE,
    )

    target_filters_group.add_argument(
        "--f-has-unlimited-scans",
        type=str.upper,
        choices=TRUTHY_VALUES + FALSY_VALUES,
        help="Filter if target has unlimited scans",
        action="store",
    )
    target_filters_group.add_argument(
        "--f-is-url-verified",
        type=str.upper,
        choices=TRUTHY_VALUES + FALSY_VALUES,
        help="Filter targets by verified (true) or not verified (false) domain",
        action="store",
    )
    target_filters_group.add_argument(
        "--f-risk",
        type=str.upper,
        choices=TargetRiskEnum.cli_input_choices(),
        help="Filter targets by risk",
        nargs=argparse.ONE_OR_MORE,
        action="store",
    )
    target_filters_group.add_argument(
        "--f-type",
        type=str.upper,
        choices=TargetTypeEnum.cli_input_choices(),
        help="Filter targets by type",
        nargs=argparse.ONE_OR_MORE,
        action="store",
    )
    target_filters_group.add_argument(
        "--f-search",
        metavar="SEARCH_TERM",
        help=TARGETS_F_SEARCH_TEXT,
        action="store",
    )
    target_filters_group.add_argument(
        "--f-label",  # TODO: make plural
        type=str,
        help="Filter Targets by Targets Label IDs",
        nargs=argparse.ONE_OR_MORE,
        action="store",
    )
    target_filters_group.add_argument(
        "--f-label-logical-operator",
        choices=LogicalOperatorTypeEnum.cli_input_choices(),
        type=str.upper,
        help="Logical operator to apply when filtering labels",
        action="store",
    )
    target_filters_group.add_argument(
        "--f-scan-profile",
        type=str,
        help="Filter Targets by Scan Profile identifiers",
        nargs=argparse.ONE_OR_MORE,
        action="store",
    )

    return target_filters_parser


def build_targets_parser():
    target_filters_parser = build_targets_filters_parser()
    configs_parser = build_configs_parser()
    file_parser = build_file_parser()
    output_parser = build_output_parser()

    targets_parser = ProbelyArgumentParser(
        prog="probely targets",
        add_help=False,
        description=TARGET_COMMAND_DESCRIPTION_TEXT,
    )

    targets_parser.set_defaults(
        command_handler=show_help,
        is_no_action_parser=True,
        parser=targets_parser,
    )

    targets_command_parser = targets_parser.add_subparsers(
        parser_class=ProbelyArgumentParser,
        title=SUB_COMMAND_AVAILABLE_ACTIONS_TITLE,
    )

    targets_get_parser = targets_command_parser.add_parser(
        "get",
        help=TARGETS_GET_COMMAND_DESCRIPTION_TEXT,
        parents=[configs_parser, target_filters_parser, output_parser],
    )
    targets_get_parser.add_argument(
        "target_ids",
        metavar="TARGET_ID",
        nargs=argparse.ZERO_OR_MORE,
        help="Identifiers of the targets to list",
    )
    targets_get_parser.set_defaults(
        command_handler=targets_get_command_handler,
        parser=targets_get_parser,
    )

    targets_add_parser = targets_command_parser.add_parser(
        "add",
        help=TARGETS_ADD_COMMAND_DESCRIPTION_TEXT,
        parents=[configs_parser, file_parser, output_parser],
    )
    targets_add_parser.add_argument(
        "target_url",
        metavar="TARGET_URL",
        nargs=argparse.OPTIONAL,
        help="Url of target",
    )
    targets_add_parser.add_argument(
        "--target-name",
        help="Display name of target",
    )
    targets_add_parser.add_argument(
        "--target-type",
        type=str.upper,
        choices=TargetTypeEnum.cli_input_choices(),
        help="Set type of target being add",
    )
    targets_add_parser.add_argument(
        "--api-schema-type",
        type=str.upper,
        choices=TargetAPISchemaTypeEnum.cli_input_choices(),
        help="Type of schema for API Targets",
    )
    targets_add_parser.add_argument(
        "--api-schema-file-url",
        help="URL to download the target's API schema",
    )

    targets_add_parser.add_argument(
        "--api-schema-file",
        metavar="FILE_PATH",
        dest="api_schema_file_path",
        help="File System Path of target's API schema (JSON or YAML)",
    )

    targets_add_parser.set_defaults(
        command_handler=targets_add_command_handler,
        parser=targets_add_parser,
    )

    targets_update_parser = targets_command_parser.add_parser(
        "update",
        help=TARGETS_UPDATE_COMMAND_DESCRIPTION_TEXT,
        parents=[configs_parser, target_filters_parser, file_parser, output_parser],
    )
    targets_update_parser.add_argument(
        "target_ids",
        metavar="TARGET_ID",
        nargs=argparse.ZERO_OR_MORE,
        help="Identifiers of the targets to update",
    )
    targets_update_parser.set_defaults(
        command_handler=targets_update_command_handler,
        parser=targets_update_parser,
    )

    start_scan_parser = targets_command_parser.add_parser(
        "start-scan",
        help=TARGETS_START_SCAN_COMMAND_DESCRIPTION_TEXT,
        parents=[configs_parser, target_filters_parser, file_parser, output_parser],
    )

    start_scan_parser.add_argument(
        "target_ids",
        metavar="TARGET_ID",
        nargs=argparse.ZERO_OR_MORE,
        help="Identifiers of the targets to scan",
    )

    start_scan_parser.set_defaults(
        command_handler=targets_start_scan_command_handler,
        parser=start_scan_parser,
    )

    follow_scan_parser = targets_command_parser.add_parser(
        "follow-scan",
        help=TARGETS_FOLLOW_SCAN_COMMAND_DESCRIPTION_TEXT,
        parents=[configs_parser, file_parser, output_parser],
    )
    follow_scan_parser.add_argument(
        "target_id",
        metavar="TARGET_ID",
        help="Identifier of target to scan and follow results",
    )
    follow_scan_parser.add_argument(
        "--timeout",
        metavar="MINUTES",
        dest="timeout_mins",
        type="positive_int",
        action="store",
        help="Maximum time to wait for the scan. If reached, the command fails and the scan is canceled",
    )
    follow_scan_parser.add_argument(
        "--severity-threshold",
        choices=FindingSeverityEnum.cli_input_choices(),
        type="cli_choice",
        action="store",
        help="Minimum vulnerability severity level required to fail the command",
    )
    follow_scan_parser.add_argument(
        "--fail-immediately",
        action="store_true",
        default=False,
        help="Fail the command when the first vulnerability meeting the threshold is found",
    )
    follow_scan_parser.add_argument(
        "--continue-scan",
        action="store_true",
        default=False,
        help="Do not cancel the scan if the command times out or fails",
    )

    follow_scan_parser.set_defaults(
        command_handler=targets_follow_scan_command_handler,
        parser=follow_scan_parser,
    )

    schedule_scan_parser = targets_command_parser.add_parser(
        "schedule-scan",
        help=TARGETS_SCHEDULE_SCAN_COMMAND_DESCRIPTION_TEXT,
        parents=[
            configs_parser,
            target_filters_parser,
            file_parser,
            output_parser,
        ],
    )
    schedule_scan_parser.add_argument(
        "target_ids",
        metavar="TARGET_ID",
        nargs=argparse.ZERO_OR_MORE,
        help="Identifiers of the targets to schedule scans",
        default=None,
    )
    schedule_scan_parser.add_argument(
        "--date-time",
        metavar=DATETIME_METAVAR,
        type=datetime.datetime.fromisoformat,
        action="store",
        help="Timestamp to start Scanning. Eg: `2020-07-05` or `2020-07-05T12:45:30`. Default to 'UTC'",
    )
    schedule_scan_parser.add_argument(
        "--timezone",
        type=str,
        action="store",
        help="'--date-time' Timezone",
    )
    schedule_scan_parser.add_argument(
        "--recurrence",
        choices=ScheduledScanRecurrenceEnum.cli_input_choices(),
        type=str.upper,
        action="store",
        help="Defines periodicity for scanning",
    )
    schedule_scan_parser.add_argument(
        "--scan-profile",
        dest="scan_profile_id",
        metavar="SCAN_PROFILE_ID",
        action="store",
        help="Scan Profile to be used in this scheduled scan",
    )
    schedule_scan_parser.add_argument(
        "--day-of-week",
        type=str.upper,
        choices=ScheduledScanDayOfWeekEnum.cli_input_choices(),
        action="store",
        help="Set specific day of week for scanning",
    )
    schedule_scan_parser.add_argument(
        "--week-of-month",
        type=str.upper,
        choices=ScheduledScanWeekOfMonthEnum.cli_input_choices(),
        action="store",
        help="Set specific week of month for scanning",
    )
    schedule_scan_parser.set_defaults(
        command_handler=targets_schedule_scan_command_handler,
        parser=schedule_scan_parser,
    )

    add_sequence_parser = targets_command_parser.add_parser(
        "add-sequence",
        help=TARGETS_ADD_SEQUENCE_COMMAND_DESCRIPTION_TEXT,
        parents=[configs_parser, target_filters_parser, file_parser, output_parser],
    )
    add_sequence_parser.add_argument(
        "target_ids",
        metavar="TARGET_ID",
        nargs=argparse.ZERO_OR_MORE,
        help="Identifiers of the targets to add the Sequence",
    )
    add_sequence_parser.add_argument(
        "--name",
        help="Display name of the sequence",
    )
    add_sequence_parser.add_argument(
        "--type",
        type=str.upper,
        choices=SequenceTypeEnum.cli_input_choices(),
        help="Set type of sequence being added",
    )
    add_sequence_parser.add_argument(
        "--enabled",
        type=str.upper,
        choices=TRUTHY_VALUES + FALSY_VALUES,
        help="Set if sequence is enabled",
    )
    add_sequence_parser.add_argument(
        "--requires-authentication",
        type=str.upper,
        choices=TRUTHY_VALUES + FALSY_VALUES,
        help="Set sequence requires scan to be authenticated",
    )

    add_sequence_parser.add_argument(
        "--sequence-steps-file",
        metavar="FILE_PATH",
        dest="sequence_steps_file_path",
        help=(
            "Sequence's content file with list of step objects. "
            "Supports 'JSON' file from 'Probely Sequence Recorder' Chrome's Extension"
        ),
    )
    add_sequence_parser.set_defaults(
        command_handler=add_sequence_command_handler,
        parser=add_sequence_parser,
    )

    add_extra_host_parser = targets_command_parser.add_parser(
        "add-extra-host",
        help=TARGETS_ADD_EXTRA_HOST_COMMAND_DESCRIPTION_TEXT,
        parents=[configs_parser, target_filters_parser, file_parser, output_parser],
    )
    add_extra_host_parser.add_argument(
        "target_ids",
        metavar="TARGET_ID",
        nargs=argparse.ZERO_OR_MORE,
        help="Identifiers of the targets to add Extra Host",
    )
    add_extra_host_parser.add_argument(
        "--host",
        help="Extra host to be added",
    )
    add_extra_host_parser.add_argument(
        "--skip-reachability-check",
        action="store_true",
        default=False,
        help="if added skips reachability check of --host parameter",
    )
    add_extra_host_parser.add_argument(
        "--include",
        type=str.upper,
        choices=TRUTHY_VALUES + FALSY_VALUES,
        help="Include the extra host in the scope of the scan",
    )
    add_extra_host_parser.add_argument(
        "--name",
        help="Display name of the extra host",
    )
    add_extra_host_parser.add_argument(
        "--description",
        help="Description of the extra host",
    )
    add_extra_host_parser.set_defaults(
        command_handler=add_extra_hosts_command_handler,
        parser=add_extra_host_parser,
    )

    targets_delete_parser = targets_command_parser.add_parser(
        "delete",
        help=TARGETS_DELETE_COMMAND_DESCRIPTION_TEXT,
        parents=[configs_parser, target_filters_parser],
    )
    targets_delete_parser.add_argument(
        "target_ids",
        metavar="TARGET_ID",
        nargs=argparse.ZERO_OR_MORE,
        help="Identifiers of the targets to delete",
    )
    targets_delete_parser.set_defaults(
        command_handler=targets_delete_command_handler,
        parser=targets_delete_parser,
    )

    return targets_parser
