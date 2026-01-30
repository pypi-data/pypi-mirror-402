import abc
from abc import ABC
from typing import Type, Optional, Dict, Union, Iterable, List

from probely.exceptions import ProbelyException
from probely.sdk.models import SDKModel


class BaseResourceMixin(ABC):
    default_query_params = None

    @property
    @abc.abstractmethod
    def model(self) -> Type[SDKModel]:
        pass


class SdkBaseManager(BaseResourceMixin, ABC):
    def _retrieve_id_from_entity_or_id(self, entity_or_id: Union[SDKModel, str]) -> str:
        if isinstance(entity_or_id, self.model):
            return str(entity_or_id.id)
        elif isinstance(entity_or_id, str):
            return entity_or_id
        else:
            raise ProbelyException(
                f"Invalid type, argument '{str(entity_or_id)}'. "
                f"Must be { self.model.__name__} or str"
            )

    def _retrieve_ids_from_entities_or_ids(
        self, entities_or_ids: Iterable[Union[SDKModel, str]]
    ) -> List[str]:
        entity_ids = []
        for entity_or_id in entities_or_ids:
            entity_id: str = self._retrieve_id_from_entity_or_id(entity_or_id)
            entity_ids.append(entity_id)

        return entity_ids


class ResourceMixin(BaseResourceMixin, ABC):
    @property
    @abc.abstractmethod
    def resource_url(self) -> str:
        pass

    def get_resource_url(self, parent_id: Optional[Dict] = None) -> str:
        """
        Construct the URL for a resource collection or a nested resource collection.
        """
        if parent_id:
            return self.resource_url.format(**parent_id)
        return self.resource_url

    @property
    @abc.abstractmethod
    def resource_detail_url(self) -> str:
        pass

    def get_resource_detail_url(self, entity_id) -> str:
        """
        Construct the URL for a single resource entity, optionally nested under a parent
        """
        return self.resource_detail_url.format(id=entity_id)


class ParentResourceMixin(BaseResourceMixin, ABC):
    @property
    @abc.abstractmethod
    def parented_resource_detail_url(self) -> str:
        pass

    def get_parented_resource_detail_url(self, target_id: str, entity_id: str) -> str:
        return self.parented_resource_detail_url.format(
            target_id=target_id, id=entity_id
        )
