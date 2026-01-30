import logging
from typing import Generator

from probely.cli.analytics.events import start_scan_used_analytics_event
from probely.cli.commands.targets.schemas import TargetApiFiltersSchema
from probely.cli.common import (
    prepare_filters_for_api,
    validate_and_retrieve_yaml_content,
)
from probely.cli.renderers import render_output
from probely.cli.tables.scan_table import ScanTable
from probely.exceptions import (
    ProbelyCLIValidation,
    ProbelyCLIFiltersNoResultsException,
    ProbelyCLIValidationFiltersAndIDsMutuallyExclusive,
)
from probely.sdk.managers import TargetManager
from probely.sdk.models import Target

logger = logging.getLogger(__name__)


def validate_and_retrieve_extra_payload(args):
    extra_payload = validate_and_retrieve_yaml_content(args.yaml_file_path)

    if "targets" in extra_payload:
        #  NOTE: This is only for alpha version, specifying Target IDs in the file will be supported in the future
        raise ProbelyCLIValidation(
            "Target IDs should be provided only through CLI, not in the YAML file."
        )

    return extra_payload


def targets_start_scan_command_handler(args):
    filters = prepare_filters_for_api(TargetApiFiltersSchema, args)
    target_ids = args.target_ids
    is_single_record_output = len(target_ids) == 1

    if not filters and not target_ids:
        raise ProbelyCLIValidation("either filters or identifiers must be provided")

    if filters and target_ids:
        raise ProbelyCLIValidationFiltersAndIDsMutuallyExclusive()

    extra_payload = validate_and_retrieve_extra_payload(args)

    if filters:
        targets_generator: Generator[Target] = TargetManager().list(filters=filters)
        first_target = next(targets_generator, None)

        if not first_target:
            start_scan_used_analytics_event(args, targets_count=0)

            raise ProbelyCLIFiltersNoResultsException()

        target_ids = [first_target.id, *[target.id for target in targets_generator]]

    start_scan_used_analytics_event(args, targets_count=len(target_ids))

    started_scans = []
    if len(target_ids) == 1:
        scan = TargetManager().start_scan(target_ids[0], extra_payload)
        started_scans.append(scan)
    else:
        started_scans = TargetManager().bulk_start_scan(target_ids, extra_payload)

    render_output(
        records=started_scans,
        table_cls=ScanTable,
        args=args,
        is_single_record_output=is_single_record_output,
    )
