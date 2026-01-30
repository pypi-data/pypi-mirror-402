import argparse
import logging
from datetime import datetime
from typing import Generator, Iterable, List, Dict, Optional

from probely.cli.commands.targets.schemas import TargetApiFiltersSchema
from probely.cli.common import (
    prepare_filters_for_api,
    validate_empty_results_generator,
    validate_and_retrieve_yaml_content,
)
from probely.cli.renderers import render_output
from probely.cli.tables.scheduled_scans import ScheduledScanTable
from probely.exceptions import (
    ProbelyCLIValidation,
    ProbelyCLIValidationFiltersAndIDsMutuallyExclusive,
)
from probely.sdk.enums import (
    ScheduledScanRecurrenceEnum,
    ScheduledScanDayOfWeekEnum,
    ScheduledScanWeekOfMonthEnum,
)
from probely.sdk.managers import TargetManager
from probely.sdk.models import Target, ScheduledScan

logger = logging.getLogger(__name__)


def _get_recurrence_argument(args, file_input: Dict):
    if args.recurrence:
        return ScheduledScanRecurrenceEnum[args.recurrence]

    recurrence_from_file = file_input.get("recurrence", None)

    if recurrence_from_file:
        try:
            return ScheduledScanRecurrenceEnum.get_by_api_response_value(
                recurrence_from_file
            )
        except ValueError:
            validation_msg = "recurrence value '{}' from file is not a valid options"
            raise ProbelyCLIValidation(validation_msg.format(recurrence_from_file))

    return None


def _get_date_time_argument(args, file_input: Dict):
    if args.date_time:
        return args.date_time

    date_time_from_file: Optional[datetime, str] = file_input.get("date_time", None)

    if not date_time_from_file:
        return None

    if isinstance(date_time_from_file, datetime):
        return date_time_from_file

    try:
        return datetime.fromisoformat(date_time_from_file)
    except Exception:
        validation_msg = "date_time value '{}' from file is not a valid options"
        raise ProbelyCLIValidation(validation_msg.format(date_time_from_file))


def _get_day_of_week_argument(args, file_input):
    if args.day_of_week:
        return ScheduledScanDayOfWeekEnum[args.day_of_week]

    day_of_week_from_file: Optional[int] = file_input.get("scheduled_day_of_week", None)

    if not day_of_week_from_file:
        return None

    try:
        return ScheduledScanDayOfWeekEnum.get_by_api_response_value(
            day_of_week_from_file
        )
    except Exception:
        validation_msg = "day_of_week value '{}' from file is not a valid options"
        raise ProbelyCLIValidation(validation_msg.format(day_of_week_from_file))


def _get_week_of_month_argument(args, file_input):
    if args.week_of_month:
        return ScheduledScanWeekOfMonthEnum[args.week_of_month]

    week_of_month_from_file: Optional[str] = file_input.get("week_index", None)

    if not week_of_month_from_file:
        return None

    try:
        return ScheduledScanWeekOfMonthEnum.get_by_api_response_value(
            week_of_month_from_file
        )
    except Exception:
        validation_msg = "week_of_month value '{}' from file is not a valid options"
        raise ProbelyCLIValidation(validation_msg.format(week_of_month_from_file))


def get_command_arguments(args: argparse.Namespace):
    file_input = {}
    if args.yaml_file_path:
        file_input = validate_and_retrieve_yaml_content(args.yaml_file_path)

    command_arguments = {
        "date_time": _get_date_time_argument(args, file_input),
        "timezone": args.timezone or file_input.get("timezone", None),
        "recurrence": _get_recurrence_argument(args, file_input),
        "day_of_week": _get_day_of_week_argument(args, file_input),
        "week_of_month": _get_week_of_month_argument(args, file_input),
        "scan_profile_id": args.scan_profile_id or file_input.get("scan_profile", None),
        "file_input": file_input,
    }

    return command_arguments


def targets_schedule_scan_command_handler(args):
    filters = prepare_filters_for_api(TargetApiFiltersSchema, args)
    targets_ids = args.target_ids
    is_single_record_output = len(targets_ids) == 1

    if not filters and not targets_ids:
        raise ProbelyCLIValidation("either filters or Target IDs must be provided.")

    if filters and targets_ids:
        raise ProbelyCLIValidationFiltersAndIDsMutuallyExclusive()

    command_arguments = get_command_arguments(args)

    if not command_arguments["date_time"]:
        raise ProbelyCLIValidation("the following arguments are required: --date-time")

    if command_arguments["day_of_week"] and not command_arguments["week_of_month"]:
        error_msg = "'--day-of-week' argument requires '--week-of-month'"
        raise ProbelyCLIValidation(error_msg)

    if command_arguments["week_of_month"] and not command_arguments["day_of_week"]:
        error_msg = "'--week-of-month' argument requires '--day-of-week'"
        raise ProbelyCLIValidation(error_msg)

    if command_arguments["day_of_week"] or command_arguments["week_of_month"]:
        if command_arguments["recurrence"] not in (
            ScheduledScanRecurrenceEnum.QUARTERLY,
            ScheduledScanRecurrenceEnum.MONTHLY,
        ):
            error_msg = "'--week-of-month' and '--day-of-week' requires MONTHLY or QUARTERLY '--recurrence'"
            raise ProbelyCLIValidation(error_msg)

    targets: Iterable[Target] = []
    if targets_ids:
        targets: Generator[Target] = TargetManager().retrieve_multiple(
            targets_or_ids=targets_ids
        )

    if filters:
        targets_generator: Generator[Target] = TargetManager().list(filters=filters)
        targets: Iterable = validate_empty_results_generator(targets_generator)

    scheduled_scans: List[ScheduledScan] = TargetManager().bulk_schedule_scan(
        targets_or_ids=list(targets),
        date_time=command_arguments["date_time"],
        timezone=command_arguments["timezone"],
        recurrence=command_arguments["recurrence"],
        day_of_week=command_arguments["day_of_week"],
        week_of_month=command_arguments["week_of_month"],
        scan_profile_id=command_arguments["scan_profile_id"],
        extra_payload=command_arguments["file_input"],
    )

    render_output(
        records=scheduled_scans,
        table_cls=ScheduledScanTable,
        args=args,
        is_single_record_output=is_single_record_output,
    )
