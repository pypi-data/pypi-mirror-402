import json
import logging
from typing import Dict, List, Generator, Iterable

from probely.cli.commands.target_sequences.schemas import SequenceApiFiltersSchema
from probely.cli.common import (
    prepare_filters_for_api,
    validate_and_retrieve_yaml_content,
    validate_empty_results_generator,
)
from probely.cli.renderers import render_output
from probely.cli.tables.sequences_table import TargetSequenceTable
from probely.exceptions import ProbelyCLIValidation
from probely.sdk.managers import TargetSequenceManager
from probely.sdk.models import TargetSequence

logger = logging.getLogger(__name__)


def target_sequences_update_command_handler(args):
    filters = prepare_filters_for_api(SequenceApiFiltersSchema, args)
    target_sequence_ids = args.sequence_ids

    if not filters and not target_sequence_ids:
        raise ProbelyCLIValidation("either filters or Sequence IDs must be provided.")

    if filters and target_sequence_ids:
        raise ProbelyCLIValidation("filters and Sequence IDs are mutually exclusive.")

    payload = validate_and_retrieve_yaml_content(args.yaml_file_path)

    logger.debug("Provided content for sequence update: %s", payload)

    sequence_steps_file_path = payload.pop("content", None)

    is_single_record_output = len(target_sequence_ids) == 1

    if sequence_steps_file_path:
        with open(sequence_steps_file_path, "r") as f:
            try:
                sequence_steps: List[Dict] = json.load(f)
            except json.decoder.JSONDecodeError:
                raise ProbelyCLIValidation("Provided file has invalid JSON content")

        payload["content"] = json.dumps(sequence_steps)

    target_sequences: Iterable[TargetSequence] = []

    if target_sequence_ids:
        target_sequences: Generator[TargetSequence] = (
            TargetSequenceManager().retrieve_multiple(target_sequence_ids)
        )

    if filters:
        target_sequences: Generator[TargetSequence] = TargetSequenceManager().list(
            filters=filters
        )
        target_sequences: Iterable = validate_empty_results_generator(target_sequences)

    target_sequences_updater: Generator[TargetSequence] = (
        TargetSequenceManager().update(sequence, payload)
        for sequence in target_sequences
    )

    render_output(
        records=target_sequences_updater,
        table_cls=TargetSequenceTable,
        args=args,
        is_single_record_output=is_single_record_output,
    )
