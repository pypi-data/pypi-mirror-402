from rich.table import Table

from probely.cli.renderers import (
    get_printable_enum_value,
    get_printable_boolean,
)
from probely.cli.tables.base_table import BaseOutputTable
from probely.constants import NOT_APPLICABLE_SMALL_OUTPUT
from probely.sdk.enums import SequenceTypeEnum
from probely.sdk.models import TargetSequence


class TargetSequenceTable(BaseOutputTable):
    @classmethod
    def create_table(cls, show_header: bool = False) -> Table:
        table = Table(show_header=show_header, box=None)

        table.add_column("ID", width=12)
        table.add_column("TARGET", width=12)
        table.add_column("NAME", width=36, no_wrap=True)
        table.add_column("TYPE", width=10)
        table.add_column("ENABLED", width=7)
        table.add_column("INDEX", width=6)

        return table

    @classmethod
    def add_row(cls, table: Table, sequence: TargetSequence) -> None:
        target_id = sequence.target.id
        table.add_row(
            sequence.id,
            target_id,
            sequence.name,
            get_printable_enum_value(SequenceTypeEnum, sequence.type),
            get_printable_boolean(sequence.enabled),
            str(sequence.index) if sequence.index else NOT_APPLICABLE_SMALL_OUTPUT,
        )
