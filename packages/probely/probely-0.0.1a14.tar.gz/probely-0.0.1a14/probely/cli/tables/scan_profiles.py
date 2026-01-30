from rich.table import Table

from probely.cli.renderers import get_printable_enum_value, get_printable_boolean
from probely.cli.tables.base_table import BaseOutputTable
from probely.sdk.enums import ScanProfileTargetTypeEnum
from probely.sdk.models import ScanProfile


class ScanProfileTable(BaseOutputTable):
    @classmethod
    def create_table(cls, show_header: bool = False) -> Table:
        table = Table(show_header=show_header, box=None)

        table.add_column("ID", width=45)
        table.add_column("IS_BUILT_IN", width=11)
        table.add_column("NAME", width=36, no_wrap=True)
        table.add_column("TARGET_TYPE", width=11)
        table.add_column("IS_ARCHIVED", width=11)

        return table

    @classmethod
    def add_row(cls, table: Table, scan_profile: ScanProfile) -> None:
        scan_profile_type = scan_profile.type.value if scan_profile.type else None
        table.add_row(
            scan_profile.id,
            get_printable_boolean(scan_profile.builtin),
            scan_profile.name,
            get_printable_enum_value(ScanProfileTargetTypeEnum, scan_profile_type),
            get_printable_boolean(scan_profile.archived),
        )
