import marshmallow

from probely.cli.schemas.base_schema import ProbelyCLIBaseFiltersSchema
from probely.cli.schemas.custom_fields import ISO8601DateTimeField, ProbelyCLIEnumField
from probely.sdk.enums import (
    FindingSeverityEnum,
    FindingStateEnum,
    LogicalOperatorTypeEnum,
    SelfReviewStatusEnum,
)


class FindingsApiFiltersSchema(ProbelyCLIBaseFiltersSchema):
    scan = marshmallow.fields.List(
        marshmallow.fields.Str(),
        allow_none=True,
        data_key="f_scans",
    )
    severity = marshmallow.fields.List(
        ProbelyCLIEnumField(FindingSeverityEnum),
        allow_none=True,
        data_key="f_severity",
    )

    state = marshmallow.fields.List(
        ProbelyCLIEnumField(FindingStateEnum),
        allow_none=True,
        data_key="f_state",
    )

    target = marshmallow.fields.List(
        marshmallow.fields.Str(),
        allow_none=True,
        data_key="f_target",
    )

    search = marshmallow.fields.Str(
        allow_none=True,
        data_key="f_search",
    )

    new = marshmallow.fields.Boolean(
        allow_none=True,
        data_key="f_is_new",
    )

    target_label = marshmallow.fields.List(
        marshmallow.fields.Str,
        allow_none=True,
        data_key="f_target_label",
    )

    target_label_logical_operator = ProbelyCLIEnumField(
        enum_class=LogicalOperatorTypeEnum,
        allow_none=True,
        data_key="f_target_label_logical_operator",
    )

    lastfound_after = ISO8601DateTimeField(
        allow_none=True,
        data_key="f_last_found_gte",
    )

    lastfound_before = ISO8601DateTimeField(
        allow_none=True,
        data_key="f_last_found_lte",
    )

    changed_after = ISO8601DateTimeField(
        allow_none=True,
        data_key="f_changed_gte",
    )

    changed_before = ISO8601DateTimeField(
        allow_none=True,
        data_key="f_changed_lte",
    )

    review_status = marshmallow.fields.List(
        ProbelyCLIEnumField(SelfReviewStatusEnum),
        allow_none=True,
        data_key="f_review_status",
    )
