from rich.table import Table

from probely.cli.renderers import (
    get_printable_date,
    get_printable_enum_value,
    get_printable_labels,
)
from probely.cli.tables.base_table import BaseOutputTable
from probely.constants import SCANS_NO_START_DATE_OUTPUT
from probely.sdk.enums import ScanStatusEnum
from probely.sdk.models import Scan


class ScanTable(BaseOutputTable):
    @classmethod
    def create_table(cls, show_header: bool = False) -> Table:
        table = Table(show_header=show_header, box=None)

        table.add_column("ID", width=12)
        table.add_column("TARGET", width=12)
        table.add_column("NAME", width=30, no_wrap=True)
        table.add_column("URL", width=30, no_wrap=True)
        table.add_column("STATUS", width=12, no_wrap=True)
        table.add_column("START_DATE", width=16)
        table.add_column("CRITICALS", width=9)
        table.add_column("HIGHS", width=5)
        table.add_column("MEDIUMS", width=7)
        table.add_column("LOWS", width=4)
        table.add_column("TARGET_LABELS", width=16, no_wrap=True)

        return table

    @classmethod
    def add_row(cls, table: Table, scan: Scan) -> None:
        target = scan.target
        site = target.site
        scan_status = scan.status.value if scan.status else None

        table.add_row(
            scan.id,
            str(target.id),
            getattr(site, "name", "N/D"),
            str(site.url),
            get_printable_enum_value(ScanStatusEnum, scan_status),
            get_printable_date(scan.started, SCANS_NO_START_DATE_OUTPUT),
            str(scan.criticals),
            str(scan.highs),
            str(scan.mediums),
            str(scan.lows),
            get_printable_labels(target.labels),
        )
