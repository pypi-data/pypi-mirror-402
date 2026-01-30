from abc import ABC, abstractmethod
from typing import Type

from rich.table import Table

from probely.sdk.models import SDKModel


class BaseOutputTable(ABC):
    @classmethod
    @abstractmethod
    def create_table(cls, show_header: bool) -> Table:
        """
        Initializes and returns a Rich Table with predefined columns.
        """
        pass

    @classmethod
    @abstractmethod
    def add_row(cls, table: Table, record: Type[SDKModel]) -> None:
        """
        Adds a single row to the provided Rich Table based on the record data.
        """
        pass
