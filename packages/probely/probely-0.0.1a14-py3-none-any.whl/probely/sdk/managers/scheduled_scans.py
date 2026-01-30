from typing import Generator, Optional, Dict, List, Union

from probely.exceptions import ProbelyRequestFailed
from probely.sdk.client import ProbelyAPIClient
from probely.sdk.managers.common import SdkBaseManager
from probely.sdk.managers.mixins.list import ListMixin
from probely.sdk.managers.mixins.retrieve_multiple import (
    RetrieveMultipleMixin,
)
from probely.sdk.models import SDKModelType
from probely.sdk.models import ScheduledScan
from probely.settings import (
    PROBELY_API_SCHEDULED_SCANS_BULK_URL,
    PROBELY_API_SCHEDULED_SCANS_DETAIL_URL,
    PROBELY_API_SCHEDULED_SCANS_URL,
)


class ScheduledScanManager(
    ListMixin,
    RetrieveMultipleMixin,
    SdkBaseManager,
):
    resource_url = PROBELY_API_SCHEDULED_SCANS_URL
    resource_detail_url = PROBELY_API_SCHEDULED_SCANS_DETAIL_URL
    parented_resource_detail_url = PROBELY_API_SCHEDULED_SCANS_DETAIL_URL
    model = ScheduledScan

    def list(
        self, filters: Optional[Dict] = None
    ) -> Generator[SDKModelType, None, None]:
        return self._list(filters=filters)

    def retrieve_multiple(
        self, scheduled_scans_or_ids: List[Union[ScheduledScan, str]]
    ):
        return self._retrieve_multiple(scheduled_scans_or_ids)

    def retrieve(
        self,
        scheduled_scan_or_id: Union[ScheduledScan, str],
    ) -> ScheduledScan:
        scheduled_scan_id = self._retrieve_id_from_entity_or_id(scheduled_scan_or_id)

        scheduled_scan: ScheduledScan = list(
            self.retrieve_multiple([scheduled_scan_id])
        )[0]

        return scheduled_scan

    def bulk_update(
        self,
        scheduled_scans_or_ids: Union[ScheduledScan, str],
        payload: Dict,
    ) -> List[ScheduledScan]:
        scheduled_scan_ids = self._retrieve_ids_from_entities_or_ids(
            scheduled_scans_or_ids
        )

        resp_status_code, resp_content = ProbelyAPIClient.patch(
            url=PROBELY_API_SCHEDULED_SCANS_BULK_URL,
            payload={
                "scheduledscans": [{"id": ss_id} for ss_id in scheduled_scan_ids],
                "scheduledscan": payload,
            },
        )

        if resp_status_code != 200:
            raise ProbelyRequestFailed(resp_content)
        scheduled_scans = [
            ScheduledScan.serializer_class(**scheduled_scan_content)
            for scheduled_scan_content in resp_content
        ]
        scheduled_scans = [ScheduledScan(ss) for ss in scheduled_scans]
        return scheduled_scans

    def bulk_delete(
        self,
        scheduled_scans_or_id: List[Union[ScheduledScan, str]],
    ) -> List[str]:
        """Delete targets

        :param scheduled_scans_or_id: Scheduled scans to be deleted.
        :type scheduleds_scans_or_id:List[Union[ScheduledScan, str]].
        """

        scheduled_scans_ids = self._retrieve_ids_from_entities_or_ids(
            scheduled_scans_or_id
        )
        resp_status_code, resp_content = ProbelyAPIClient.delete(
            url=PROBELY_API_SCHEDULED_SCANS_BULK_URL,
            payload={
                "scheduledscans": [{"id": ss_id} for ss_id in scheduled_scans_ids],
            },
        )

        if resp_status_code != 204:
            raise ProbelyRequestFailed(resp_content)

        return scheduled_scans_ids
