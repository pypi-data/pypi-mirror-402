from typing import Dict, List, Generator, Union

from probely.sdk.managers.common import SdkBaseManager
from probely.sdk.managers.mixins.delete import ParentedDeleteMixin

from probely.settings import (
    PROBELY_API_EXTRA_HOSTS_DETAIL_URL,
    PROBELY_API_ACCOUNT_EXTRA_HOSTS_URL,
    PROBELY_API_EXTRA_HOSTS_URL,
)
from probely.sdk.models import TargetExtraHost
from probely.sdk.managers.mixins.list import ListMixin
from probely.sdk.managers.mixins.retrieve_multiple import RetrieveMultipleMixin
from probely.sdk.managers.mixins.update import ParentedUpdateMixin


class TargetExtraHostManager(
    ListMixin,
    RetrieveMultipleMixin,
    ParentedUpdateMixin,
    ParentedDeleteMixin,
    SdkBaseManager,
):
    resource_url = PROBELY_API_ACCOUNT_EXTRA_HOSTS_URL
    resource_detail_url = PROBELY_API_EXTRA_HOSTS_DETAIL_URL
    parented_resource_url = PROBELY_API_EXTRA_HOSTS_URL
    parented_resource_detail_url = PROBELY_API_EXTRA_HOSTS_DETAIL_URL
    model = TargetExtraHost
    default_query_params = {"include": "target"}

    def list(self, filters: Dict) -> Generator[TargetExtraHost, None, None]:
        # TODO: specific and validate filters
        return self._list(filters=filters)

    def retrieve_multiple(
        self, target_extra_hosts_or_ids: List[Union[TargetExtraHost, str]]
    ) -> Generator[TargetExtraHost, None, None]:
        return self._retrieve_multiple(target_extra_hosts_or_ids)

    def update(
        self, target_extra_host_or_id: Union[TargetExtraHost, str], payload: Dict
    ) -> TargetExtraHost:
        extra_host: TargetExtraHost

        if isinstance(target_extra_host_or_id, TargetExtraHost):
            extra_host = target_extra_host_or_id
        else:
            extra_host = list(self.retrieve_multiple([target_extra_host_or_id]))[0]

        return self._parented_update(
            target_id=extra_host.target.id, entity_id=extra_host.id, payload=payload
        )

    def delete(self, target_extra_host_or_id: Union[TargetExtraHost, str]) -> None:
        extra_host: TargetExtraHost

        if isinstance(target_extra_host_or_id, TargetExtraHost):
            extra_host = target_extra_host_or_id
        else:
            extra_host = list(self.retrieve_multiple([target_extra_host_or_id]))[0]

        self._parented_delete(target_id=extra_host.target.id, entity_id=extra_host.id)
