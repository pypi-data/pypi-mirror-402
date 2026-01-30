from typing import Generator

from probely.cli.commands.targets.schemas import TargetLabelApiFiltersSchema
from probely.cli.common import prepare_filters_for_api
from probely.cli.renderers import render_output
from probely.cli.tables.target_labels import TargetLabelsTable
from probely.exceptions import ProbelyCLIValidation
from probely.sdk.managers import TargetLabelManager
from probely.sdk.models import TargetLabel


def target_labels_get_command_handler(args):
    """
    Lists all accessible target labels of client
    """
    filters = prepare_filters_for_api(TargetLabelApiFiltersSchema, args)
    target_labels_ids = args.target_label_ids

    if filters and target_labels_ids:
        raise ProbelyCLIValidation(
            "filters and Target Label IDs are mutually exclusive."
        )

    is_single_record_output = len(target_labels_ids) == 1

    if target_labels_ids:
        target_labels: Generator[TargetLabel] = TargetLabelManager().retrieve_multiple(
            target_labels_ids
        )
    else:
        target_labels: Generator[TargetLabel] = TargetLabelManager().list(
            filters=filters
        )

    render_output(
        records=target_labels,
        table_cls=TargetLabelsTable,
        args=args,
        is_single_record_output=is_single_record_output,
    )
