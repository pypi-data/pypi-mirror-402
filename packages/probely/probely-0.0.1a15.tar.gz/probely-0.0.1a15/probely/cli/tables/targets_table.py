from rich.table import Table

from probely.cli.renderers import (
    get_printable_enum_value,
    get_printable_labels,
    get_printable_last_scan_date,
)
from probely.cli.tables.base_table import BaseOutputTable
from probely.sdk.enums import TargetRiskEnum
from probely.sdk.models import Target


class TargetTable(BaseOutputTable):
    @classmethod
    def create_table(cls, show_header: bool = False) -> Table:
        table = Table(show_header=show_header, box=None)

        table.add_column("ID", width=12)
        table.add_column("NAME", width=36, no_wrap=True)
        table.add_column("URL", width=48, no_wrap=True)
        table.add_column("RISK", width=8)
        table.add_column("LAST_SCAN", width=16)
        table.add_column("LABELS", width=16, no_wrap=True)

        return table

    @classmethod
    def add_row(cls, table: Table, target: Target) -> None:
        site = target.site

        table.add_row(
            target.id,
            site.name,
            str(site.url),
            get_printable_enum_value(TargetRiskEnum, target.risk),
            get_printable_last_scan_date(target),
            get_printable_labels(target.labels),
        )
