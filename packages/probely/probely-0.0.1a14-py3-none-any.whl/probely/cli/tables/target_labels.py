from rich.table import Table

from probely.cli.tables.base_table import BaseOutputTable
from probely.sdk.models import TargetLabel


class TargetLabelsTable(BaseOutputTable):
    @classmethod
    def create_table(cls, show_header: bool = False) -> Table:
        table = Table(show_header=show_header, box=None)

        table.add_column("ID", width=12)
        table.add_column("NAME", width=36, no_wrap=True)
        table.add_column("COLOR", width=48, no_wrap=True)

        return table

    @classmethod
    def add_row(cls, table: Table, label: TargetLabel) -> None:
        table.add_row(
            label.id,
            label.name,
            label.color,
        )
