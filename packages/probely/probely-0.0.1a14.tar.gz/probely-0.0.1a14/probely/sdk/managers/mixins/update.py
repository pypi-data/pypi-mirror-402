import abc
from abc import ABC
from typing import Dict

from probely.exceptions import (
    ProbelyBadRequest,
    ProbelyObjectsNotFound,
    ProbelyRequestFailed,
)
from probely.sdk.client import ProbelyAPIClient
from probely.sdk.managers.common import (
    ResourceMixin,
    SdkBaseManager,
    ParentResourceMixin,
)
from probely.sdk.models import SDKModelType


class UpdateABC(SdkBaseManager, ABC):
    @abc.abstractmethod
    def update(self, *args, **kwargs):
        pass


class UpdateMixin(UpdateABC, ResourceMixin, ABC):
    def _update(
        self,
        entity_or_id: str,
        payload: Dict = None,
    ) -> SDKModelType:
        entity_id = self._retrieve_id_from_entity_or_id(entity_or_id)

        query_params = self.default_query_params
        url = self.get_resource_detail_url(entity_id)

        resp_status_code, resp_content = ProbelyAPIClient.patch(
            url, query_params=query_params, payload=payload
        )

        if resp_status_code == 400:
            raise ProbelyBadRequest(resp_content)
        if resp_status_code == 404:
            raise ProbelyObjectsNotFound(entity_id)
        if resp_status_code != 200:
            raise ProbelyRequestFailed(resp_content)

        deserialized_data = self.model.serializer_class(**resp_content)
        return self.model(deserialized_data)


class ParentedUpdateMixin(UpdateABC, ParentResourceMixin, ABC):
    def _parented_update(
        self,
        target_id,
        entity_id,
        payload: Dict = None,
    ) -> SDKModelType:
        url = self.get_parented_resource_detail_url(target_id, entity_id)
        query_params = self.default_query_params

        resp_status_code, resp_content = ProbelyAPIClient.patch(
            url, query_params=query_params, payload=payload
        )

        if resp_status_code == 400:
            raise ProbelyBadRequest(resp_content)
        if resp_status_code == 404:
            raise ProbelyObjectsNotFound(entity_id)
        if resp_status_code != 200:
            raise ProbelyRequestFailed(resp_content)

        deserialized_data = self.model.serializer_class(**resp_content)
        return self.model(deserialized_data)
