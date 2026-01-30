import abc
from typing import List, Generator, Union

from probely.constants import ID_404_VALIDATION
from probely.sdk.managers.common import ResourceMixin, SdkBaseManager
from probely.sdk.models import SDKModelType


class RetrieveMultipleABC(SdkBaseManager, abc.ABC):
    @abc.abstractmethod
    def retrieve_multiple(self, *args, **kwargs):
        pass


class RetrieveMultipleMixin(RetrieveMultipleABC, ResourceMixin, abc.ABC):
    def _retrieve_multiple(
        self,
        entities_or_ids: List[Union[SDKModelType, str]],
    ) -> Generator[SDKModelType, None, None]:
        f"""
        Efficient way to retrieve multiple entities by ID.

        Only possible for API endpoints with 'id' filters
        and '{ID_404_VALIDATION}' flag
        """

        entities_ids = self._retrieve_ids_from_entities_or_ids(entities_or_ids)

        filters = {
            "id": entities_ids,
            ID_404_VALIDATION: True,
        }
        return self.list(filters=filters)


class RetrieveMultipleMultipleRequestsMixin(
    RetrieveMultipleABC,
    ResourceMixin,
    abc.ABC,
):
    def _retrieve_multiple_multiple_requests(
        self,
        entities_or_ids: List[Union[SDKModelType, str]],
    ) -> List[SDKModelType]:
        """
        Retrieve multiple resources by their IDs.

        Avoid using unless API is not ready for CLI yet.
        """

        entities_ids = self._retrieve_ids_from_entities_or_ids(entities_or_ids)

        values = [self.retrieve(entity_id) for entity_id in entities_ids]
        return values
