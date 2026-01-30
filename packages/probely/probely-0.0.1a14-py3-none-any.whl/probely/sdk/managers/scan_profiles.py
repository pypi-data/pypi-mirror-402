from typing import Generator, Dict, Union, List, Optional

from probely.sdk.managers.common import SdkBaseManager
from probely.sdk.models import ScanProfile
from probely.settings import (
    PROBELY_API_SCAN_PROFILES_DETAIL_URL,
    PROBELY_API_SCAN_PROFILES_URL,
)
from probely.sdk.managers.mixins.list import ListMixin
from probely.sdk.managers.mixins.retrieve import RetrieveByIDMixin
from probely.sdk.managers.mixins.retrieve_multiple import (
    RetrieveMultipleMultipleRequestsMixin,
)


class ScanProfileManager(
    ListMixin,
    RetrieveMultipleMultipleRequestsMixin,
    RetrieveByIDMixin,
    SdkBaseManager,
):
    resource_url = PROBELY_API_SCAN_PROFILES_URL
    resource_detail_url = PROBELY_API_SCAN_PROFILES_DETAIL_URL
    model = ScanProfile

    def list(
        self, filters: Optional[Dict] = None
    ) -> Generator[ScanProfile, None, None]:
        # TODO: specific and validate filters
        return self._list(filters=filters)

    def retrieve_multiple(
        self, scan_profiles_or_ids: List[Union[ScanProfile, str]]
    ) -> List[ScanProfile]:
        return self._retrieve_multiple_multiple_requests(scan_profiles_or_ids)

    def retrieve(self, scan_profiles_or_ids: Union[ScanProfile, str]) -> ScanProfile:
        return self._retrieve_by_id(scan_profiles_or_ids)
