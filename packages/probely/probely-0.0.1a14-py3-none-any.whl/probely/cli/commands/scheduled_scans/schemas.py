import marshmallow

from probely.cli.schemas.base_schema import ProbelyCLIBaseFiltersSchema


class ScheduledScanApiFiltersSchema(ProbelyCLIBaseFiltersSchema):
    search = marshmallow.fields.Str(
        allow_none=True,
        data_key="f_search",
    )
    target = marshmallow.fields.List(
        marshmallow.fields.Str(),
        allow_none=True,
        data_key="f_target",
    )
    label = marshmallow.fields.List(
        marshmallow.fields.Str,
        allow_none=True,
        data_key="f_target_label",
    )
