import abc
from typing import Optional, Dict, Generator


from probely.exceptions import ProbelyRequestFailed
from probely.sdk.client import ProbelyAPIClient
from probely.sdk.helpers import validate_id_404_response
from probely.sdk.managers.common import ResourceMixin
from probely.sdk.models import SDKModelType
from probely.settings import PROBELY_API_PAGE_SIZE


class ListABC(abc.ABC):
    @abc.abstractmethod
    def list(self, *args, **kwargs) -> Generator[SDKModelType, None, None]:
        pass


class ListMixin(ListABC, ResourceMixin, abc.ABC):
    def _list(
        self,
        parent_id: Optional[Dict] = None,
        filters: Optional[Dict] = None,
        ordering: Optional[str] = None,
    ) -> Generator[SDKModelType, None, None]:
        url = self.get_resource_url(parent_id)
        filters = filters or {}
        page = 1

        if not ordering:
            ordering = getattr(self, "listing_ordering", "-changed")

        params = {
            "ordering": ordering,
            "length": PROBELY_API_PAGE_SIZE,
            "page": 1,
            **(self.default_query_params if self.default_query_params else {}),
            **filters,
        }

        while True:
            resp_status_code, resp_content = ProbelyAPIClient.get(
                url, query_params=params
            )

            validate_id_404_response(status_code=resp_status_code, content=resp_content)

            if resp_status_code != 200:
                raise ProbelyRequestFailed(reason=resp_content)

            results = resp_content.get("results", [])
            total_pages_count = resp_content.get("page_total", 1)

            for item in results:
                deserialized_data = self.model.serializer_class(**item)
                yield self.model(deserialized_data)

            if page >= total_pages_count:
                break

            page += 1
            params["page"] = page
