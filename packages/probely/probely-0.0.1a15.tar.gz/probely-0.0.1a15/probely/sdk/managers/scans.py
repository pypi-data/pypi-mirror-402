from typing import Any, Dict, Generator, List, Optional, Union


from probely.exceptions import (
    ProbelyObjectsNotFound,
    ProbelyRequestFailed,
)

from probely.constants import ID_404_VALIDATION
from probely.sdk.managers.common import SdkBaseManager
from probely.settings import (
    PROBELY_API_SCAN_CANCEL_URL_TEMPLATE,
    PROBELY_API_SCAN_PAUSE_URL_TEMPLATE,
    PROBELY_API_SCAN_RESUME_URL_TEMPLATE,
    PROBELY_API_SCANS_BULK_CANCEL_URL,
    PROBELY_API_SCANS_BULK_PAUSE_URL,
    PROBELY_API_SCANS_BULK_RESUME_URL,
    PROBELY_API_SCANS_DETAIL_URL,
    PROBELY_API_SCANS_URL,
)
from probely.sdk.client import ProbelyAPIClient
from probely.sdk.helpers import (
    validate_id_404_response,
)
from probely.sdk.managers.mixins.retrieve import RetrieveByIDMixin
from probely.sdk.models import Scan
from probely.sdk.managers.mixins.list import ListMixin
from probely.sdk.managers.mixins.retrieve_multiple import RetrieveMultipleMixin


class ScanManager(
    RetrieveByIDMixin,
    RetrieveMultipleMixin,
    ListMixin,
    SdkBaseManager,
):
    resource_url = PROBELY_API_SCANS_URL
    resource_detail_url = PROBELY_API_SCANS_DETAIL_URL
    model = Scan

    def list(self, filters: Optional[Dict] = None) -> Generator[Scan, None, None]:
        # TODO: specify and validate filters
        return self._list(filters=filters)

    def retrieve_multiple(
        self, scans_or_ids: List[Union[Scan, str]]
    ) -> Generator[Scan, None, None]:
        return self._retrieve_multiple(scans_or_ids)

    def retrieve(self, scan_or_id: Union[Scan, str]) -> Scan:
        return self._retrieve_by_id(scan_or_id)

    def _single_action(
        self,
        scan_or_id: Union[Scan, str],
        endpoint_template: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Scan:
        """
        Perform a single action (cancel, pause, resume) on a Scan.

        :param scan_or_id: The Scan object or scan ID.
        :param endpoint_template: The endpoint URL template with placeholders.
        :param payload: Optional payload for actions that require additional data.
        :return: The updated Scan object
        """

        scan = (
            self._retrieve_by_id(scan_or_id)
            if isinstance(scan_or_id, str)
            else scan_or_id
        )

        action_endpoint = endpoint_template.format(target_id=scan.target.id, id=scan.id)
        resp_status_code, resp_content = ProbelyAPIClient.post(
            action_endpoint, payload=payload
        )

        if resp_status_code == 404:
            raise ProbelyObjectsNotFound(scan.id)

        if resp_status_code != 200:
            raise ProbelyRequestFailed(resp_content, resp_status_code)

        deserialized_data = self.model.serializer_class(**resp_content)
        return self.model(deserialized_data)

    def _bulk_action(
        self,
        scans_or_ids: List[Union[str, Scan]],
        bulk_action_url: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Generator[Scan, None, None]:
        """
        Perform a bulk action (cancel, pause, resume) on multiple scans.

        :param scans_or_ids: A list of Scan objects or scan IDs.
        :param bulk_action_url: The bulk action endpoint URL.
        :param payload: Optional payload for actions that require additional data.
        :return: A list of updated Scan objects.
        """

        scan_ids = self._retrieve_ids_from_entities_or_ids(scans_or_ids)

        payload_data = {"scans": [{"id": scan_id} for scan_id in scan_ids]}

        if payload:
            payload_data.update(payload)

        resp_status_code, resp_content = ProbelyAPIClient.post(
            bulk_action_url,
            payload=payload_data,
            query_params={ID_404_VALIDATION: True},
        )

        validate_id_404_response(status_code=resp_status_code, content=resp_content)

        if resp_status_code != 200:
            raise ProbelyRequestFailed(resp_content)

        return self.retrieve_multiple(scan_ids)

    def cancel(self, scan: Union[Scan, str]) -> Scan:
        return self._single_action(scan, PROBELY_API_SCAN_CANCEL_URL_TEMPLATE)

    def pause(self, scan: Union[Scan, str]) -> Scan:
        return self._single_action(scan, PROBELY_API_SCAN_PAUSE_URL_TEMPLATE)

    def resume(
        self, scan: Union[Scan, str], ignore_blackout_period: bool = False
    ) -> Scan:
        return self._single_action(
            scan,
            PROBELY_API_SCAN_RESUME_URL_TEMPLATE,
            payload={"ignore_blackout_period": ignore_blackout_period},
        )

    def bulk_cancel(self, scans: List[Union[str, Scan]]) -> Generator[Scan, None, None]:
        return self._bulk_action(scans, PROBELY_API_SCANS_BULK_CANCEL_URL)

    def bulk_pause(self, scans: List[Union[str, Scan]]) -> Generator[Scan, None, None]:
        return self._bulk_action(scans, PROBELY_API_SCANS_BULK_PAUSE_URL)

    def bulk_resume(
        self,
        scans: List[Union[str, Scan]],
        ignore_blackout_period: bool = False,
    ) -> Generator[Scan, None, None]:
        return self._bulk_action(
            scans,
            PROBELY_API_SCANS_BULK_RESUME_URL,
            payload={
                "overrides": {"ignore_blackout_period": ignore_blackout_period},
            },
        )
