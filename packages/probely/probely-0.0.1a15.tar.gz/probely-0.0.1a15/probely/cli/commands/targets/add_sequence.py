import argparse
import json
import logging
from typing import Dict, Generator, List, Iterable

from probely.cli.common import (
    prepare_filters_for_api,
    validate_and_retrieve_yaml_content,
    validate_empty_results_generator,
)
from probely.cli.renderers import render_output
from probely.cli.tables.sequences_table import TargetSequenceTable
from probely.exceptions import ProbelyCLIValidation
from probely.sdk.enums import SequenceTypeEnum
from probely.sdk.managers.targets import TargetManager
from probely.cli.commands.targets.schemas import TargetApiFiltersSchema
from probely.sdk.models import Target, TargetSequence

logger = logging.getLogger(__name__)


def get_type(args, file_input):
    if args.type:  # should be validated by argparse
        return SequenceTypeEnum[args.type]

    if file_input.get("type", None):
        try:
            sequence_type = SequenceTypeEnum.get_by_api_response_value(
                file_input.get("type")
            )
            return sequence_type
        except ValueError:
            raise ProbelyCLIValidation(
                "sequence type '{}' from file is not a valid option".format(
                    file_input["type"]
                )
            )


def _get_sequence_steps_from_path(args, file_input):
    # We pop because we allow file path on the content where API receives objects
    sequence_steps_file_path = file_input.pop("content", None)

    if args.sequence_steps_file_path:
        sequence_steps_file_path = args.sequence_steps_file_path

    if not sequence_steps_file_path:
        raise ProbelyCLIValidation("'sequence-steps-file' is required")

    with open(sequence_steps_file_path, "r") as f:
        try:
            sequence_steps: List[Dict] = json.load(f)
        except json.decoder.JSONDecodeError:
            raise ProbelyCLIValidation("Provided file has invalid JSON content")

    file_input["content"] = json.dumps(sequence_steps)

    return sequence_steps


def generate_payload_from_args(args: argparse.Namespace) -> Dict:
    """
    Generate payload for creating Sequence by prioritizing command line arguments
    and using file input as a fallback.
    """
    file_input = validate_and_retrieve_yaml_content(args.yaml_file_path)

    command_arguments = {
        "target_ids": args.target_ids,
        "name": args.name or file_input.get("name"),
        "type": get_type(args, file_input),
        "enabled": args.enabled or file_input.get("enabled"),
        "sequence_steps": _get_sequence_steps_from_path(args, file_input),
        "requires_authentication": args.requires_authentication
        or file_input.get("requires_authentication"),
        "extra_payload": file_input,
    }

    return command_arguments


def add_sequence_command_handler(args: argparse.Namespace):
    filters = prepare_filters_for_api(TargetApiFiltersSchema, args)
    targets_ids = args.target_ids
    is_single_record_output = len(targets_ids) == 1

    if not filters and not targets_ids:
        raise ProbelyCLIValidation("either filters or Target IDs must be provided.")

    if filters and targets_ids:
        raise ProbelyCLIValidation("filters and Target IDs are mutually exclusive.")

    payload = generate_payload_from_args(args)

    logger.debug("sequence add extra_payload: {}".format(payload["extra_payload"]))

    if not payload["name"]:
        raise ProbelyCLIValidation("'name' is required")

    targets: Iterable[Target] = []

    if targets_ids:
        targets: Generator[Target] = TargetManager().retrieve_multiple(targets_ids)

    if filters:
        targets_generator: Generator[Target] = TargetManager().list(filters=filters)
        targets: Iterable[Target] = validate_empty_results_generator(targets_generator)

    sequences = []
    for target in targets:
        sequence: TargetSequence = TargetManager().add_sequence(
            target_or_id=target,
            name=payload["name"],
            sequence_steps=payload["sequence_steps"],
            sequence_type=payload["type"],
            enabled=payload["enabled"],
            requires_authentication=payload["requires_authentication"],
            extra_payload=payload["extra_payload"],
        )
        sequences.append(sequence)

    render_output(
        records=sequences,
        table_cls=TargetSequenceTable,
        args=args,
        is_single_record_output=is_single_record_output,
    )
