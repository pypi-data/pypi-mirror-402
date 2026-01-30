from rich.table import Table

from probely.cli.renderers import get_printable_boolean
from probely.cli.tables.base_table import BaseOutputTable
from probely.constants import NOT_APPLICABLE_SMALL_OUTPUT, UNKNOWN_VALUE_OUTPUT
from probely.sdk.models import TargetExtraHost


class TargetExtraHostTable(BaseOutputTable):
    @classmethod
    def create_table(cls, show_header: bool = False) -> Table:
        table = Table(show_header=show_header, box=None)

        table.add_column("ID", width=12)
        table.add_column("TARGET", width=12)
        table.add_column("NAME", width=36, no_wrap=True)
        table.add_column("VERIFIED", width=8)
        table.add_column("HOST", width=48, no_wrap=True)
        table.add_column("INCLUDED", width=8)

        return table

    @classmethod
    def add_row(cls, table: Table, extra_host: TargetExtraHost) -> None:
        table.add_row(
            extra_host.id,
            extra_host.target.id if extra_host.target else UNKNOWN_VALUE_OUTPUT,
            extra_host.name if extra_host.name else NOT_APPLICABLE_SMALL_OUTPUT,
            get_printable_boolean(extra_host.verified),
            extra_host.host,
            get_printable_boolean(extra_host.include),
        )
