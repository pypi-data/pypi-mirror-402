from abc import ABC, abstractmethod

from probely.exceptions import ProbelyObjectsNotFound, ProbelyRequestFailed
from probely.sdk.client import ProbelyAPIClient
from probely.sdk.managers.common import (
    ParentResourceMixin,
    ResourceMixin,
    SdkBaseManager,
)


class DeleteABC(ABC):
    @abstractmethod
    def delete(self, *args, **kwargs):
        pass


class DeleteMixin(DeleteABC, SdkBaseManager, ResourceMixin, ABC):
    def _delete(self, entity_or_id: str) -> None:
        entity_id = self._retrieve_id_from_entity_or_id(entity_or_id)

        url = self.get_resource_detail_url(entity_id)
        resp_status_code, resp_content = ProbelyAPIClient.delete(url=url)

        if resp_status_code == 404:
            raise ProbelyObjectsNotFound(entity_id)

        if resp_status_code != 204:
            raise ProbelyRequestFailed(reason=resp_content)


class ParentedDeleteMixin(DeleteABC, ParentResourceMixin, ABC):
    def _parented_delete(self, target_id, entity_id) -> None:
        url = self.get_parented_resource_detail_url(target_id, entity_id)
        resp_status_code, resp_content = ProbelyAPIClient.delete(url=url)

        if resp_status_code == 404:
            raise ProbelyObjectsNotFound(entity_id)

        if resp_status_code != 204:
            raise ProbelyRequestFailed(reason=resp_content)
