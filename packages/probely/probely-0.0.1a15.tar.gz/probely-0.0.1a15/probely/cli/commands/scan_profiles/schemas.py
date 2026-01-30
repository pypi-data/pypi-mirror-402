import marshmallow

from probely.cli.schemas.base_schema import ProbelyCLIBaseFiltersSchema
from probely.cli.schemas.custom_fields import ProbelyCLIEnumField
from probely.sdk.enums import ScanProfileTargetTypeEnum


class CanScanUnverifiedTargetsFiled(marshmallow.fields.Boolean):
    def _serialize(self, value, attr, obj, **kwargs):
        raise NotImplementedError()

    def _deserialize(self, value, attr, data, **kwargs):
        # APIs "verified" filter naming is confusing as it allows to only show
        # scans profiles for unverified targets
        # So it was changed to --f-can-scan-unverified-targets on the CLI.
        # This renaming implies inverting the filter value
        if value is True:
            return False


class ScanProfileApiFiltersSchema(ProbelyCLIBaseFiltersSchema):
    search = marshmallow.fields.Str(
        allow_none=True,
        data_key="f_search",
    )
    type = ProbelyCLIEnumField(
        ScanProfileTargetTypeEnum,
        allow_none=True,
        data_key="f_type",
    )
    builtin = marshmallow.fields.Boolean(
        allow_none=True,
        data_key="f_is_built_in",
    )
    verified = CanScanUnverifiedTargetsFiled(
        allow_none=True,
        data_key="f_can_scan_unverified_targets",
    )

    archived = marshmallow.fields.Boolean(
        allow_none=True,
        data_key="f_is_archived",
    )
