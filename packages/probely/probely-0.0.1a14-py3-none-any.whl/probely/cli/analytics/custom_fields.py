from typing import Type

import marshmallow

from probely.sdk.enums import ProbelyCLIEnum


class AnalyticsCLIEnumField(marshmallow.fields.Enum):
    enum_class: Type[ProbelyCLIEnum]

    def __init__(self, enum_class: Type[ProbelyCLIEnum], *args, **kwargs):
        self.enum_class = enum_class
        super().__init__(enum=enum_class, *args, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            return str(self.enum_class[value].cli_choice).lower()
        except Exception:
            return None


class AnalyticsTrueIfExistsField(marshmallow.fields.Field):
    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, str):
            return True

        if isinstance(value, list):
            return True if len(value) > 0 else marshmallow.missing

        if isinstance(value, dict):
            return True if len(value.keys()) > 0 else marshmallow.missing

        if isinstance(value, int):
            return True

        if isinstance(value, float):
            return True

        if isinstance(value, bool):
            return value

        return marshmallow.missing


class AnalyticsFlagField(marshmallow.fields.Field):
    """
    Field for flags that can be set to True but default to False.
    False doesn't mean User selected that
    """

    def _deserialize(self, value, attr, data, **kwargs):
        if value is True:
            return True
        return marshmallow.missing  # value will not be added to resulting dict
