import argparse
from typing import Generator, Iterable

from probely.cli.commands.target_extra_hosts.schemas import (
    TargetExtraHostsApiFiltersSchema,
)
from probely.cli.common import prepare_filters_for_api, validate_empty_results_generator
from probely.exceptions import (
    ProbelyCLIValidation,
    ProbelyCLIValidationFiltersAndIDsMutuallyExclusive,
)
from probely.sdk.managers import TargetExtraHostManager
from probely.sdk.models import TargetExtraHost


def target_extra_hosts_delete_command_handler(args: argparse.Namespace):
    filters = prepare_filters_for_api(TargetExtraHostsApiFiltersSchema, args)
    target_extra_hosts_ids = args.extra_hosts_ids

    if not filters and not target_extra_hosts_ids:
        raise ProbelyCLIValidation(
            "either filters or Target Extra Hosts IDs must be provided."
        )

    if filters and target_extra_hosts_ids:
        raise ProbelyCLIValidationFiltersAndIDsMutuallyExclusive()

    target_extra_hosts: Iterable = []

    if filters:
        filtered_target_extra_hosts: Generator[TargetExtraHost] = (
            TargetExtraHostManager().list(filters=filters)
        )

        target_extra_hosts: Iterable = validate_empty_results_generator(
            filtered_target_extra_hosts
        )
    else:
        target_extra_hosts: Generator[TargetExtraHost] = (
            TargetExtraHostManager().retrieve_multiple(target_extra_hosts_ids)
        )

    for target_extra_host in target_extra_hosts:
        TargetExtraHostManager().delete(target_extra_host_or_id=target_extra_host)
        args.console.print(target_extra_host.id)
