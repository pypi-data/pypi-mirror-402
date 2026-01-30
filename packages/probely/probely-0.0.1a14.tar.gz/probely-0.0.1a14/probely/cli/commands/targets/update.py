import logging
from typing import Generator, List, Iterable

from probely.cli.commands.targets.schemas import TargetApiFiltersSchema
from probely.cli.common import (
    prepare_filters_for_api,
    validate_and_retrieve_yaml_content,
    validate_empty_results_generator,
)
from probely.cli.renderers import render_output
from probely.cli.tables.targets_table import TargetTable
from probely.exceptions import ProbelyCLIValidation
from probely.sdk.managers import TargetManager
from probely.sdk.models import Target

logger = logging.getLogger(__name__)


def _update_and_render(args, targets_or_ids, payload, single_id_command: bool = False):
    if len(targets_or_ids) == 1:
        updated_targets: List[Target] = [
            TargetManager().update(target_or_id=targets_or_ids[0], payload=payload)
        ]
    else:
        updated_targets: Generator[Target] = TargetManager().bulk_update(
            targets_or_ids=targets_or_ids, payload=payload
        )

    render_output(
        records=updated_targets,
        table_cls=TargetTable,
        args=args,
        is_single_record_output=single_id_command,
    )


def targets_update_command_handler(args):
    """
    Update targets based on the provided filters or target IDs.
    """
    filters = prepare_filters_for_api(TargetApiFiltersSchema, args)
    targets_ids = args.target_ids
    single_id_command = len(targets_ids) == 1

    if not filters and not targets_ids:
        raise ProbelyCLIValidation("either filters or Target IDs must be provided.")

    if filters and targets_ids:
        raise ProbelyCLIValidation("filters and Target IDs are mutually exclusive.")

    yaml_file_path = args.yaml_file_path
    if not yaml_file_path:
        raise ProbelyCLIValidation(
            "Path to the YAML file that contains the payload is required."
        )
    payload = validate_and_retrieve_yaml_content(yaml_file_path)

    logger.debug("Provided content for target update: %s", payload)

    if targets_ids:
        single_id_command = len(targets_ids) == 1
        _update_and_render(args, targets_ids, payload, single_id_command)
        return

    targets_generator: Generator[Target] = TargetManager().list(filters=filters)
    targets: Iterable[Target] = validate_empty_results_generator(targets_generator)

    _update_and_render(args, list(targets), payload, single_id_command)
