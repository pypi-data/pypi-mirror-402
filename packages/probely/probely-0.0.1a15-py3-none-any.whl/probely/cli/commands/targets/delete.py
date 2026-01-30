from typing import Generator

from probely.cli.commands.targets.schemas import TargetApiFiltersSchema
from probely.cli.common import prepare_filters_for_api
from probely.exceptions import ProbelyCLIValidation, ProbelyCLIFiltersNoResultsException
from probely.sdk.managers import TargetManager
from probely.sdk.models import Target


def targets_delete_command_handler(args):
    filters = prepare_filters_for_api(TargetApiFiltersSchema, args)
    targets_ids = args.target_ids

    if not filters and not targets_ids:
        raise ProbelyCLIValidation("Expected target_ids or filters")

    if filters and targets_ids:
        raise ProbelyCLIValidation("filters and Target IDs are mutually exclusive.")

    if filters:
        targets: Generator[Target] = TargetManager().list(filters=filters)
        first_target = next(targets, None)

        if not first_target:
            raise ProbelyCLIFiltersNoResultsException()

        targets_ids = [first_target.id] + [target.id for target in targets]

    if len(targets_ids) == 1:
        TargetManager().delete(targets_ids[0])
        args.console.print(targets_ids[0])
        return

    deleted_targets_ids = TargetManager().bulk_delete(targets_ids)

    for target_id in deleted_targets_ids:
        args.console.print(target_id)
