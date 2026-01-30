import argparse
from itertools import chain
import json
from pathlib import Path
from typing import Type, Union, Generator, Iterable
from probely.sdk.enums import (
    APISchemaFileFormatEnum,
)
import marshmallow
import yaml

import probely.settings as settings
from probely.exceptions import ProbelyCLIValidation, ProbelyCLIFiltersNoResultsException


def _validate_file_path(file_path: Union[str, None]) -> Path:
    file_path: Path = Path(file_path)

    if not file_path.exists():
        raise ProbelyCLIValidation("provided path does not exist: {}".format(file_path))

    if not file_path.is_file():
        raise ProbelyCLIValidation(
            "Provided path is not a file: {}".format(file_path.absolute())
        )

    if file_path.suffix not in settings.CLI_ACCEPTED_FILE_EXTENSIONS:
        raise ProbelyCLIValidation(
            "Invalid file extension, must be one of the following: {}:".format(
                settings.CLI_ACCEPTED_FILE_EXTENSIONS
            )
        )

    return file_path


def validate_and_retrieve_schema_file_content(file_path: Union[str, None]):
    if not file_path:
        return dict(), None

    file_path: Path = _validate_file_path(file_path)

    if file_path.suffix in settings.YAML_FILE_EXTENSIONS:
        schema_file_format = APISchemaFileFormatEnum.YAML
    elif file_path.suffix in settings.JSON_FILE_EXTENSIONS:
        schema_file_format = APISchemaFileFormatEnum.JSON
    else:
        raise ProbelyCLIValidation(
            "Invalid file extension, must be one of the following: {}:".format(
                settings.CLI_ACCEPTED_FILE_EXTENSIONS
            )
        )

    with file_path.open() as file:
        if schema_file_format == APISchemaFileFormatEnum.YAML:
            try:
                schema_file_content = yaml.safe_load(file)
            except yaml.error.YAMLError as ex:
                raise ProbelyCLIValidation(
                    "Invalid YAML content in Schema File: {}".format(ex)
                )
        elif schema_file_format == APISchemaFileFormatEnum.JSON:
            try:
                schema_file_content = json.load(file)
            except json.JSONDecodeError as ex:
                raise ProbelyCLIValidation(
                    "Invalid JSON content in Schema File: {}".format(ex)
                )

    if schema_file_content is None:
        raise ProbelyCLIValidation("file {} is empty.".format(file_path))

    return schema_file_content, schema_file_format


def validate_and_retrieve_yaml_content(yaml_file_path: Union[str, None]):
    if not yaml_file_path:
        return dict()

    file_path: Path = _validate_file_path(yaml_file_path)

    with file_path.open() as yaml_file:
        try:
            yaml_content = yaml.safe_load(yaml_file)
        except yaml.error.YAMLError as ex:
            raise ProbelyCLIValidation("Invalid YAML content in file: {}".format(ex))

    if yaml_content is None:
        raise ProbelyCLIValidation("YAML file {} is empty.".format(file_path))

    return yaml_content


def validate_empty_results_generator(results_generator: Generator) -> Iterable:
    first_result = next(results_generator, None)

    if first_result is None:
        raise ProbelyCLIFiltersNoResultsException()

    return chain([first_result], results_generator)


def prepare_filters_for_api(
    schema: Type[marshmallow.Schema], args: argparse.Namespace
) -> dict:
    """
    Prepares and validates filters using the provided Marshmallow schema.
    """
    filters_schema = schema()
    try:
        filters = filters_schema.load(vars(args))
        return filters
    except marshmallow.ValidationError as ex:
        raise ProbelyCLIValidation(f"Invalid filters: {ex}")
