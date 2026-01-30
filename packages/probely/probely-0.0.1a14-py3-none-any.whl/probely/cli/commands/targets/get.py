from typing import Generator

from probely.cli.commands.targets.schemas import TargetApiFiltersSchema
from probely.cli.common import prepare_filters_for_api
from probely.cli.renderers import render_output
from probely.cli.tables.targets_table import TargetTable
from probely.exceptions import ProbelyCLIValidationFiltersAndIDsMutuallyExclusive
from probely.sdk.managers import TargetManager
from probely.sdk.models import Target


def targets_get_command_handler(args):
    """
    Lists all accessible targets of client
    """
    filters = prepare_filters_for_api(TargetApiFiltersSchema, args)
    targets_ids = args.target_ids
    is_single_record_output = len(targets_ids) == 1

    if filters and targets_ids:
        raise ProbelyCLIValidationFiltersAndIDsMutuallyExclusive()

    if targets_ids:
        targets: Generator[Target] = TargetManager().retrieve_multiple(targets_ids)
    else:
        targets: Generator[Target] = TargetManager().list(filters=filters)

    render_output(
        records=targets,
        table_cls=TargetTable,
        args=args,
        is_single_record_output=is_single_record_output,
    )
