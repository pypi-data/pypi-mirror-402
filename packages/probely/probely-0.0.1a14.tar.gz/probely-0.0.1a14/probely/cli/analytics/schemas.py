import marshmallow
from marshmallow.fields import Integer

from probely.cli.analytics.custom_fields import (
    AnalyticsCLIEnumField,
    AnalyticsTrueIfExistsField,
    AnalyticsFlagField,
)
from probely.cli.enums import OutputEnum
from probely.cli.schemas.base_schema import ProbelyCLIBaseFiltersSchema
from probely.sdk.enums import (
    FindingSeverityEnum,
    LogicalOperatorTypeEnum,
    TargetTypeEnum,
    TargetRiskEnum,
)


class AnalyticsSchema(ProbelyCLIBaseFiltersSchema):
    @marshmallow.post_load
    def ignore_unused_filters(self, data, **kwargs):
        """
        All argparse arguments default to None, which means they must be removed.
        This avoids errors when calling the API.
        """
        command_filters = {f: v for f, v in data.items() if v is not None}
        return command_filters

    class Meta:
        unknown = marshmallow.EXCLUDE


class AnalyticsTargetsFiltersSchema(AnalyticsSchema):
    has_unlimited_scans = marshmallow.fields.Boolean(
        allow_none=True,
        data_key="f_has_unlimited_scans",
    )

    is_url_verified = marshmallow.fields.Boolean(
        allow_none=True, data_key="f_is_url_verified"
    )

    risk = marshmallow.fields.List(
        AnalyticsCLIEnumField(TargetRiskEnum),
        allow_none=True,
        data_key="f_risk",
    )

    type = marshmallow.fields.List(
        AnalyticsCLIEnumField(TargetTypeEnum),
        allow_none=True,
        data_key="f_type",
    )

    search = AnalyticsTrueIfExistsField(allow_none=True, data_key="f_search")

    label = AnalyticsTrueIfExistsField(allow_none=True, data_key="f_label")

    label_logical_operator = AnalyticsCLIEnumField(
        LogicalOperatorTypeEnum,
        allow_none=True,
        data_key="f_label_logical_operator",
    )

    scan_profile = AnalyticsTrueIfExistsField(
        allow_none=True, data_key="f_scan_profile"
    )


class _AnalyticsArgumentsBaseSchema(AnalyticsSchema):
    api_key = AnalyticsTrueIfExistsField(allow_none=True, data_key="api_key")
    debug = AnalyticsFlagField(allow_none=True, data_key="debug")
    file_input = AnalyticsTrueIfExistsField(allow_none=True, data_key="yaml_file_path")
    output = AnalyticsCLIEnumField(
        OutputEnum,
        allow_none=True,
        data_key="output_format",
    )


class AnalyticsStarScanArgumentsSchema(_AnalyticsArgumentsBaseSchema):
    pass


class AnalyticsFollowScanArgumentsSchema(_AnalyticsArgumentsBaseSchema):
    timeout = Integer(allow_none=True, data_key="timeout_mins")
    severity_threshold = AnalyticsCLIEnumField(
        FindingSeverityEnum,
        allow_none=True,
        data_key="severity_threshold",
    )
    fail_immediately = AnalyticsFlagField(
        allow_none=True,
        data_key="fail_immediately",
    )
    continue_scan = AnalyticsFlagField(
        allow_none=True,
        data_key="continue_scan",
    )
