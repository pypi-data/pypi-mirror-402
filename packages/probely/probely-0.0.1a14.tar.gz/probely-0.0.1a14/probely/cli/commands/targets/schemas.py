import marshmallow

from probely.cli.schemas.base_schema import ProbelyCLIBaseFiltersSchema
from probely.cli.schemas.custom_fields import ProbelyCLIEnumField
from probely.sdk.enums import TargetRiskEnum, TargetTypeEnum, LogicalOperatorTypeEnum


class TargetApiFiltersSchema(ProbelyCLIBaseFiltersSchema):
    scan_profile = marshmallow.fields.List(
        marshmallow.fields.Str,
        allow_none=True,
        data_key="f_scan_profile",
    )
    label = marshmallow.fields.List(
        marshmallow.fields.Str,
        allow_none=True,
        data_key="f_label",
    )
    label_logical_operator = ProbelyCLIEnumField(
        enum_class=LogicalOperatorTypeEnum,
        allow_none=True,
        data_key="f_label_logical_operator",
    )
    unlimited = marshmallow.fields.Boolean(
        allow_none=True,
        data_key="f_has_unlimited_scans",
    )
    verified = marshmallow.fields.Boolean(
        allow_none=True,
        data_key="f_is_url_verified",
    )
    risk = marshmallow.fields.List(
        ProbelyCLIEnumField(TargetRiskEnum),
        allow_none=True,
        data_key="f_risk",
    )
    type = marshmallow.fields.List(
        ProbelyCLIEnumField(TargetTypeEnum),
        allow_none=True,
        data_key="f_type",
    )
    search = marshmallow.fields.Str(
        allow_none=True,
        data_key="f_search",
    )


class TargetLabelApiFiltersSchema(ProbelyCLIBaseFiltersSchema):
    search = marshmallow.fields.Str(
        allow_none=True,
        data_key="f_search",
    )
