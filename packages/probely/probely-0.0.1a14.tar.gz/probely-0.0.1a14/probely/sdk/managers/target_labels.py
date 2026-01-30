from typing import Union, Dict, Generator, Optional, List

from mergedeep import Strategy, merge

from probely.exceptions import (
    ProbelyBadRequest,
    ProbelyRequestFailed,
)

from probely.sdk.managers.common import SdkBaseManager
from probely.sdk.managers.mixins.delete import DeleteMixin
from probely.settings import (
    PROBELY_API_TARGET_LABELS_DETAIL_URL,
    PROBELY_API_TARGET_LABELS_URL,
)
from probely.sdk.client import ProbelyAPIClient
from probely.sdk.models import TargetLabel
from probely.sdk.managers.mixins.list import ListMixin
from probely.sdk.managers.mixins.update import UpdateMixin
from probely.sdk.managers.mixins.retrieve import RetrieveByIDMixin
from probely.sdk.managers.mixins.retrieve_multiple import RetrieveMultipleMixin


class TargetLabelManager(
    ListMixin,
    RetrieveByIDMixin,
    RetrieveMultipleMixin,
    DeleteMixin,
    UpdateMixin,
    SdkBaseManager,
):
    resource_url = PROBELY_API_TARGET_LABELS_URL
    resource_detail_url = PROBELY_API_TARGET_LABELS_DETAIL_URL
    model = TargetLabel

    def list(
        self, filters: Optional[Dict] = None
    ) -> Generator[TargetLabel, None, None]:
        return self._list(filters=filters)

    def retrieve_multiple(
        self,
        target_labels_or_ids: List[Union[TargetLabel, str]],
    ) -> Generator[TargetLabel, None, None]:
        return self._retrieve_multiple(target_labels_or_ids)

    def retrieve(self, target_label_or_id: Union[TargetLabel, str]) -> TargetLabel:
        return self._retrieve_by_id(target_label_or_id)

    def update(
        self,
        target_label_or_id: Union[TargetLabel, str],
        payload: Dict,
    ) -> TargetLabel:
        return self._update(target_label_or_id, payload)

    def delete(self, target_label_or_id: Union[TargetLabel, str]) -> None:
        self._delete(target_label_or_id)

    def create(
        self,
        name: str,
        color: Union[str, None] = None,
        extra_payload: Union[dict, None] = None,
    ) -> TargetLabel:
        """Creates new target label

        :param name: label name.
        :type name: str.
        :param color: color of target label.
        :type color: str, optional.
        :param extra_payload: allows customization of request. Content should follow api request body
        :type extra_payload: Optional[dict].
        :raise: ProbelyBadRequest.
        :return: Created target label content.

        """

        body_data = {}
        if extra_payload:
            body_data = extra_payload

        arguments_settings = {
            "name": name,
        }
        if color:
            arguments_settings["color"] = color

        merge(body_data, arguments_settings, strategy=Strategy.REPLACE)

        resp_status_code, resp_content = ProbelyAPIClient.post(
            url=self.resource_url, payload=body_data
        )

        if resp_status_code == 400:
            raise ProbelyBadRequest(response_payload=resp_content)

        if resp_status_code != 201:
            raise ProbelyRequestFailed(resp_content)

        deserialized_data = self.model.serializer_class(**resp_content)
        return self.model(deserialized_data)
