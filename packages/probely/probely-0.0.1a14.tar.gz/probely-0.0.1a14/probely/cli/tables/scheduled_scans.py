from rich.table import Table

from probely.cli.renderers import (
    get_printable_date,
    get_printable_enum_value,
)
from probely.cli.tables.base_table import BaseOutputTable
from probely.constants import UNKNOWN_VALUE_OUTPUT
from probely.sdk.enums import ScheduledScanRecurrenceEnum
from probely.sdk.models import ScheduledScan


class ScheduledScanTable(BaseOutputTable):
    @classmethod
    def create_table(cls, show_header: bool = False) -> Table:
        table = Table(show_header=show_header, box=None)

        table.add_column("ID", width=12)
        table.add_column("TARGET", width=12)
        table.add_column("NEXT_SCAN", width=16)
        table.add_column("RECURRENCE", width=10)
        table.add_column("TIMEZONE", width=64)

        return table

    @classmethod
    def add_row(cls, table: Table, scheduled_scan: ScheduledScan) -> None:
        timezone = scheduled_scan.timezone
        table.add_row(
            scheduled_scan.id,
            scheduled_scan.target.id,
            get_printable_date(scheduled_scan.date_time),
            get_printable_enum_value(
                ScheduledScanRecurrenceEnum,
                scheduled_scan.recurrence.value,
            ),
            timezone if timezone else UNKNOWN_VALUE_OUTPUT,
        )
