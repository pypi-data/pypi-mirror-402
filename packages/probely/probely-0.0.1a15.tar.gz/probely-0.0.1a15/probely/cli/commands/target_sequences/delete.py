from typing import Generator, Iterable

from probely.cli.commands.target_sequences.schemas import SequenceApiFiltersSchema
from probely.cli.common import prepare_filters_for_api, validate_empty_results_generator
from probely.exceptions import ProbelyCLIValidation
from probely.sdk.managers import TargetSequenceManager
from probely.sdk.models import TargetSequence


def target_sequences_delete_command_handler(args):
    filters = prepare_filters_for_api(SequenceApiFiltersSchema, args)
    target_sequence_ids = args.sequence_ids

    if not filters and not target_sequence_ids:
        raise ProbelyCLIValidation("either filters or Sequence IDs must be provided.")

    if filters and target_sequence_ids:
        raise ProbelyCLIValidation("Filters and Sequence IDs are mutually exclusive.")

    if target_sequence_ids:
        target_sequences: Generator[TargetSequence] = (
            TargetSequenceManager().retrieve_multiple(target_sequence_ids)
        )

    if filters:
        target_sequences: Generator[TargetSequence] = TargetSequenceManager().list(
            filters=filters
        )
        target_sequences: Iterable = validate_empty_results_generator(target_sequences)

    for target_sequence in target_sequences:
        TargetSequenceManager().delete(target_sequence_or_id=target_sequence)
        args.console.print(target_sequence.id)
