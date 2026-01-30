import argparse
import sys
import textwrap
from datetime import datetime
from itertools import chain
from typing import Iterable, List, Optional, Type, Union

import yaml
from dateutil import parser
from rich.console import Console

from probely.cli.enums import OutputEnum
from probely.cli.tables.base_table import BaseOutputTable
from probely.constants import (
    TARGET_NEVER_SCANNED_OUTPUT,
    UNKNOWN_VALUE_OUTPUT,
    FALSE_VALUE_OUTPUT,
    TRUE_VALUE_OUTPUT,
    UNKNOWN_LABELS_OUTPUT,
    NOT_APPLICABLE_SMALL_OUTPUT,
)
from probely.sdk.enums import ProbelyCLIEnum
from probely.sdk.models import SDKModel, Target
from probely.sdk.schemas import FindingLabelDataModel, TargetLabelDataModel
from probely.settings import (
    CLI_DEFAULT_OUTPUT_FORMAT,
    CLI_JSON_OUTPUT_INDENT_SIZE,
    CLI_YAML_OUTPUT_INDENT_SIZE,
)


class OutputRenderer:
    """
    Class responsible for rendering output in various formats (JSON, YAML, TABLE, IDS).
    """

    def __init__(
        self,
        records: Iterable[SDKModel],
        output_type: Optional[OutputEnum],
        console: Console,
        table_cls: Type[BaseOutputTable],
        is_single_record_output: bool = False,
    ):
        self.records = records
        self.table_cls = table_cls
        self.console = console
        self.output_type = output_type
        self.is_single_record_output = is_single_record_output

    def render(self) -> None:
        if self.output_type == OutputEnum.JSON:
            self._render_json()
        elif self.output_type == OutputEnum.YAML:
            self._render_yaml()
        elif self.output_type == OutputEnum.IDS_ONLY:
            self._render_ids_only()
        else:
            self._render_table()

    def _render_ids_only(self) -> None:
        for record in self.records:
            self.console.print(record.id)

    def _build_printable_json(
        self,
        record: SDKModel,
        add_trailing_comma: bool = False,
    ) -> str:
        list_base_indent: str = " " * CLI_JSON_OUTPUT_INDENT_SIZE

        record_json = record.to_json(indent=CLI_JSON_OUTPUT_INDENT_SIZE)
        indented_json_lines = [
            list_base_indent + line for line in record_json.split("\n")
        ]

        if add_trailing_comma:
            indented_json_lines[-1] = indented_json_lines[-1] + ","

        printable_json = "\n".join(indented_json_lines)

        return printable_json

    def _json_empty_results_output(self):
        if self.is_single_record_output:
            self.console.print("{}")
            return

        self.console.print("[]")
        return

    def _render_json(self) -> None:
        records = iter(self.records)

        try:
            last_record = next(records)
        except StopIteration:
            self._json_empty_results_output()
            return

        if self.is_single_record_output:
            self.console.print(last_record.to_json(indent=CLI_JSON_OUTPUT_INDENT_SIZE))
            return

        self.console.print("[")

        for next_record in records:
            record_json = self._build_printable_json(
                last_record,
                add_trailing_comma=True,
            )
            self.console.print(record_json)

            last_record = next_record

        record_json = self._build_printable_json(
            last_record,
            add_trailing_comma=False,
        )
        self.console.print(record_json)

        self.console.print("]")

    def _render_yaml(self) -> None:
        records = iter(self.records)

        self.console.print("---")

        try:
            first_record = next(records)
        except StopIteration:
            return

        if self.is_single_record_output:
            record_dict = first_record.to_dict(mode="json")
            self.console.print(
                yaml.dump(
                    record_dict,
                    indent=CLI_YAML_OUTPUT_INDENT_SIZE,
                    width=sys.maxsize,
                ).rstrip("\n")
            )
            return

        for record in chain([first_record], records):
            record_dict = record.to_dict(mode="json")
            self.console.print(
                yaml.dump(
                    [record_dict],  # prints in list format
                    indent=CLI_YAML_OUTPUT_INDENT_SIZE,
                    width=sys.maxsize,
                ).rstrip("\n")
            )

    def _render_table(self) -> None:
        records_iterator = iter(self.records)
        first_record_table = self.table_cls.create_table(show_header=True)

        try:
            first_record = next(records_iterator)
            self.table_cls.add_row(first_record_table, first_record)
        except StopIteration:
            pass

        self.console.print(first_record_table)  # always prints the header

        for record in records_iterator:
            table = self.table_cls.create_table(show_header=False)
            self.table_cls.add_row(table, record)
            self.console.print(table)


def render_output(
    records: Iterable[SDKModel],
    args: argparse.Namespace,
    table_cls: Type[BaseOutputTable],
    is_single_record_output: bool = False,
) -> None:
    """
    Helper function to render output without repeating common parameters.
    """
    console = args.console

    default_output_format = OutputEnum[CLI_DEFAULT_OUTPUT_FORMAT]
    output_type = (
        OutputEnum[args.output_format] if args.output_format else default_output_format
    )

    renderer = OutputRenderer(
        records=records,
        output_type=output_type,
        console=console,
        table_cls=table_cls,
        is_single_record_output=is_single_record_output,
    )
    renderer.render()


def get_printable_enum_value(enum: Type[ProbelyCLIEnum], api_enum_value: str) -> str:
    try:
        value_name: str = enum.get_by_api_response_value(api_enum_value).name
        return value_name
    except ValueError:
        return UNKNOWN_VALUE_OUTPUT  # TODO: scenario that risk enum updated but CLI is forgotten


def get_printable_labels(
    labels: List[Union[TargetLabelDataModel, FindingLabelDataModel]] = None,
) -> str:
    if labels is None:
        return UNKNOWN_LABELS_OUTPUT

    labels_names = []
    try:
        for label in labels:
            truncated_label = textwrap.shorten(label.name, width=16, placeholder="...")
            labels_names.append(truncated_label)
    except Exception:
        return UNKNOWN_LABELS_OUTPUT

    printable_labels = ", ".join(labels_names)

    return printable_labels


def get_printable_date(
    date_input: Union[str, datetime, None],
    default_string: Union[str, None] = None,
) -> str:
    if isinstance(date_input, str):
        date_obj = parser.isoparse(date_input)
    elif isinstance(date_input, datetime):
        date_obj = date_input
    else:
        date_obj = None

    if date_obj:
        return date_obj.strftime("%Y-%m-%d %H:%M")

    if default_string:
        return default_string

    return NOT_APPLICABLE_SMALL_OUTPUT


def get_printable_last_scan_date(target: Target) -> str:
    if not target.last_scan:
        return TARGET_NEVER_SCANNED_OUTPUT

    return get_printable_date(target.last_scan.started, TARGET_NEVER_SCANNED_OUTPUT)


def get_printable_boolean(bool_var: bool):
    if bool_var is True:
        return TRUE_VALUE_OUTPUT
    elif bool_var is False:
        return FALSE_VALUE_OUTPUT
    else:
        return UNKNOWN_VALUE_OUTPUT
