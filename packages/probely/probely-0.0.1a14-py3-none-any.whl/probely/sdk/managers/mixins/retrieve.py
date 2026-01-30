import abc

from probely.exceptions import ProbelyObjectsNotFound, ProbelyRequestFailed
from probely.sdk.client import ProbelyAPIClient
from probely.sdk.managers.common import ResourceMixin, SdkBaseManager
from probely.sdk.models import SDKModelType


class RetrieveABC(SdkBaseManager):
    @abc.abstractmethod
    def retrieve(self, *args, **kwargs):
        pass


class RetrieveByIDMixin(RetrieveABC, ResourceMixin, abc.ABC):
    def _retrieve_by_id(self, entity_or_id: str) -> SDKModelType:
        entity_id = self._retrieve_id_from_entity_or_id(entity_or_id)

        url = self.get_resource_detail_url(entity_id)

        resp_status_code, resp_content = ProbelyAPIClient.get(
            url, query_params=self.default_query_params
        )

        if resp_status_code == 404:
            raise ProbelyObjectsNotFound(entity_id)

        if resp_status_code != 200:
            raise ProbelyRequestFailed(reason=resp_content)

        deserialized_data = self.model.serializer_class(**resp_content)
        return self.model(deserialized_data)
