import marshmallow

from probely.cli.schemas.base_schema import ProbelyCLIBaseFiltersSchema


class TargetExtraHostsApiFiltersSchema(ProbelyCLIBaseFiltersSchema):
    target = marshmallow.fields.List(
        marshmallow.fields.Str,
        allow_none=True,
        data_key="f_target",
    )
