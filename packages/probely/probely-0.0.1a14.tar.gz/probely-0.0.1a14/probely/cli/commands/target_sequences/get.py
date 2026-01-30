from typing import Generator

from probely.cli.commands.target_sequences.schemas import SequenceApiFiltersSchema
from probely.cli.common import prepare_filters_for_api
from probely.cli.renderers import render_output
from probely.cli.tables.sequences_table import TargetSequenceTable
from probely.exceptions import ProbelyCLIValidation
from probely.sdk.managers import TargetSequenceManager
from probely.sdk.models import TargetSequence


def target_sequences_get_command_handler(args):
    """
    Lists all target's sequences.
    """
    filters = prepare_filters_for_api(SequenceApiFiltersSchema, args)
    sequence_ids = args.sequence_ids

    if filters and sequence_ids:
        raise ProbelyCLIValidation("filters and Sequence IDs are mutually exclusive.")

    is_single_record_output = len(sequence_ids) == 1

    if sequence_ids:
        sequences: Generator[TargetSequence] = (
            TargetSequenceManager().retrieve_multiple(sequence_ids)
        )
    else:
        sequences: Generator[TargetSequence] = TargetSequenceManager().list(
            filters=filters
        )

    render_output(
        records=sequences,
        table_cls=TargetSequenceTable,
        args=args,
        is_single_record_output=is_single_record_output,
    )
