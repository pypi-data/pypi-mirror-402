import marshmallow

from probely.cli.schemas.base_schema import ProbelyCLIBaseFiltersSchema
from probely.cli.schemas.custom_fields import ProbelyCLIEnumField
from probely.sdk.enums import SequenceTypeEnum


class SequenceApiFiltersSchema(ProbelyCLIBaseFiltersSchema):
    enabled = marshmallow.fields.Boolean(
        allow_none=True,
        data_key="f_enabled",
    )
    name = marshmallow.fields.Str(
        allow_none=True,
        data_key="f_name",
    )
    type = ProbelyCLIEnumField(
        enum_class=SequenceTypeEnum,
        allow_none=True,
        data_key="f_type",
    )
    target = marshmallow.fields.List(
        marshmallow.fields.Str,
        allow_none=True,
        data_key="f_target",
    )
