import argparse
import logging
from typing import Dict, Optional

from probely.cli.common import (
    validate_and_retrieve_schema_file_content,
    validate_and_retrieve_yaml_content,
)
from probely.cli.renderers import render_output
from probely.cli.tables.targets_table import TargetTable
from probely.exceptions import ProbelyCLIValidation
from probely.sdk.enums import TargetAPISchemaTypeEnum, TargetTypeEnum
from probely.sdk.managers import TargetManager
from probely.sdk.models import Target

logger = logging.getLogger(__name__)


def validate_and_retrieve_api_scan_settings(
    target_type,
    api_schema_file_url,
    api_schema_file_path,
    api_schema_type,
):
    api_schema_settings: Dict = dict()

    if target_type != TargetTypeEnum.API:
        return api_schema_settings

    has_schema_file = api_schema_file_url or api_schema_file_path

    if not has_schema_file:
        msg = "API Targets require 'api_schema_file_url' or 'api_schema_file'"
        raise ProbelyCLIValidation(msg)

    if api_schema_file_url and api_schema_file_path:
        msg = "'api_schema_file_url' and 'api_schema_file' are mutually exclusive"
        raise ProbelyCLIValidation(msg)

    if has_schema_file and not api_schema_type:
        raise ProbelyCLIValidation("API schema file require 'api_schema_type'")

    api_schema_settings["api_schema_type"] = api_schema_type
    api_schema_settings["api_schema_file_url"] = api_schema_file_url
    api_schema_settings["api_schema_file_path"] = api_schema_file_path

    return api_schema_settings


def get_target_type(args, file_input):
    if args.target_type:  # should be validated by argparse
        return TargetTypeEnum[args.target_type]

    if file_input.get("type", None):
        try:
            target_type = TargetTypeEnum.get_by_api_response_value(
                file_input.get("type")
            )
            return target_type
        except ValueError:
            raise ProbelyCLIValidation(
                "target type '{}' from file is not a valid options".format(
                    file_input["type"]
                )
            )

    return TargetTypeEnum.WEB


def get_api_schema_type(args, file_input):
    if args.api_schema_type:
        return TargetAPISchemaTypeEnum[args.api_schema_type]

    api_schema_type_from_file: Optional[str] = (
        file_input.get("site", {})
        .get("api_scan_settings", {})
        .get("api_schema_type", None)
    )

    if api_schema_type_from_file:
        try:
            return TargetAPISchemaTypeEnum.get_by_api_response_value(
                api_schema_type_from_file
            )
        except ValueError:
            validation_msg = "API schema type '{}' from file is not a valid options"
            raise ProbelyCLIValidation(validation_msg.format(api_schema_type_from_file))

    return None


def get_command_arguments(args: argparse.Namespace):
    file_input = {}
    if args.yaml_file_path:
        file_input = validate_and_retrieve_yaml_content(args.yaml_file_path)

    api_schema_file_url = args.api_schema_file_url or file_input.get("site", {}).get(
        "api_scan_settings", {}
    ).get("api_schema_url", None)

    api_schema_file_path = args.api_schema_file_path or file_input.get("site", {}).get(
        "api_scan_settings", {}
    ).get("api_schema_file", None)

    command_arguments = {
        "target_url": args.target_url or file_input.get("site", {}).get("url", None),
        "target_name": args.target_name or file_input.get("site", {}).get("name", None),
        "target_type": get_target_type(args, file_input),
        "api_schema_type": get_api_schema_type(args, file_input),
        "api_schema_file_url": api_schema_file_url,
        "api_schema_file_path": api_schema_file_path,
        "file_input": file_input,
    }

    return command_arguments


def targets_add_command_handler(args: argparse.Namespace):
    command_arguments = get_command_arguments(args)

    if not command_arguments["target_url"]:
        raise ProbelyCLIValidation("must provide a target URL by argument or yaml-file")

    api_scan_settings = validate_and_retrieve_api_scan_settings(
        target_type=command_arguments.get("target_type"),
        api_schema_file_url=command_arguments.get("api_schema_file_url"),
        api_schema_file_path=command_arguments.get("api_schema_file_path"),
        api_schema_type=command_arguments.get("api_schema_type"),
    )

    logger.debug("target add extra_payload: {}".format(command_arguments["file_input"]))

    api_schema_file_content = None
    api_schema_file_format = None
    if api_scan_settings.get("api_schema_file_path"):
        api_schema_file_content, api_schema_file_format = (
            validate_and_retrieve_schema_file_content(
                api_scan_settings.get("api_schema_file_path")
            )
        )

    target: Target = TargetManager().create(
        target_url=command_arguments["target_url"],
        target_name=command_arguments["target_name"],
        target_type=command_arguments["target_type"],
        api_schema_type=api_scan_settings.get("api_schema_type", None),
        api_schema_file_url=api_scan_settings.get("api_schema_file_url", None),
        api_schema_file_content=api_schema_file_content,
        api_schema_file_content_format=api_schema_file_format,
        extra_payload=command_arguments["file_input"],
    )

    render_output(
        records=[target],
        table_cls=TargetTable,
        args=args,
        is_single_record_output=True,
    )
