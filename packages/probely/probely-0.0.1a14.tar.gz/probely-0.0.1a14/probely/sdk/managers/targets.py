from datetime import datetime
from io import BytesIO
import json
from typing import Dict, Generator, List, Union, Optional

import yaml
from mergedeep import Strategy, merge

from probely.exceptions import (
    ProbelyBadRequest,
    ProbelyObjectsNotFound,
    ProbelyRequestFailed,
    ProbelyValidation,
)

from probely.constants import ID_404_VALIDATION
from probely.sdk.managers.common import SdkBaseManager
from probely.sdk.managers.mixins.delete import DeleteMixin
from probely.settings import (
    PROBELY_API_SCANS_BULK_START_URL,
    PROBELY_API_SEQUENCES_URL,
    PROBELY_API_TARGETS_BULK_DELETE_URL,
    PROBELY_API_TARGETS_BULK_UPDATE_URL,
    PROBELY_API_TARGETS_DETAIL_URL,
    PROBELY_API_TARGETS_START_SCAN_URL,
    PROBELY_API_TARGETS_UPLOAD_API_SCHEMA_FILE_URL,
    PROBELY_API_TARGETS_URL,
    PROBELY_API_SCHEDULED_SCANS_BULK_CREATE_URL,
    PROBELY_API_EXTRA_HOSTS_URL,
)
from probely.sdk.client import ProbelyAPIClient
from probely.sdk.helpers import (
    validate_id_404_response,
)
from probely.sdk.models import (
    Scan,
    Target,
    TargetSequence,
    ScheduledScan,
    TargetExtraHost,
)
from probely.sdk.enums import (
    APISchemaFileFormatEnum,
    SequenceTypeEnum,
    TargetTypeEnum,
    ScheduledScanRecurrenceEnum,
    TargetAPISchemaTypeEnum,
    ScheduledScanDayOfWeekEnum,
    ScheduledScanWeekOfMonthEnum,
)

from probely.sdk.managers.mixins.list import ListMixin
from probely.sdk.managers.mixins.update import UpdateMixin
from probely.sdk.managers.mixins.retrieve import RetrieveByIDMixin
from probely.sdk.managers.mixins.retrieve_multiple import RetrieveMultipleMixin


class TargetManager(
    RetrieveByIDMixin,
    RetrieveMultipleMixin,
    ListMixin,
    DeleteMixin,
    UpdateMixin,
    SdkBaseManager,
):
    resource_url = PROBELY_API_TARGETS_URL
    resource_detail_url = PROBELY_API_TARGETS_DETAIL_URL
    model = Target

    def list(self, filters: Optional[Dict] = None) -> Generator[Target, None, None]:
        # TODO: specify and validate filters
        return self._list(filters=filters)

    def retrieve_multiple(
        self, targets_or_ids: List[Union[Target, str]]
    ) -> Generator[Target, None, None]:
        return self._retrieve_multiple(targets_or_ids)

    def retrieve(self, target_or_id: Union[Target, str]) -> Target:
        return self._retrieve_by_id(target_or_id)

    def update(self, target_or_id: Union[Target, str], payload) -> Target:
        return self._update(target_or_id, payload)

    def delete(self, target_or_id: Union[Target, str]) -> None:
        self._delete(target_or_id)

    def bulk_delete(
        self,
        targets_or_ids: List[Union[Target, str]],
    ) -> List[str]:
        """Delete targets

        :param targets_or_ids: targets to be deleted.
        :type targets_or_ids:List[Union[Target, str]].
        """

        target_ids = self._retrieve_ids_from_entities_or_ids(targets_or_ids)

        resp_status_code, resp_content = ProbelyAPIClient.post(
            url=PROBELY_API_TARGETS_BULK_DELETE_URL,
            query_params={ID_404_VALIDATION: True},
            payload={
                "ids": target_ids,
            },
        )

        validate_id_404_response(status_code=resp_status_code, content=resp_content)

        if resp_status_code != 200:
            raise ProbelyRequestFailed(resp_content)

        deleted_targets_ids = resp_content.get("ids", [])

        return deleted_targets_ids

    def bulk_update(
        self,
        targets_or_ids: List[Union[Target, str]],
        payload: Dict,
    ) -> Generator[Target, None, None]:
        target_ids = self._retrieve_ids_from_entities_or_ids(targets_or_ids)

        resp_status_code, resp_content = ProbelyAPIClient.post(
            url=PROBELY_API_TARGETS_BULK_UPDATE_URL,
            query_params={ID_404_VALIDATION: True},
            payload={"ids": target_ids, **payload},
        )

        validate_id_404_response(status_code=resp_status_code, content=resp_content)

        if resp_status_code == 400:
            raise ProbelyBadRequest(resp_content)

        if resp_status_code != 200:
            raise ProbelyRequestFailed(resp_content)

        updated_targets_ids = resp_content.get("ids", [])

        targets: Generator[Target] = self.retrieve_multiple(updated_targets_ids)

        return targets

    def _upload_api_schema_file(
        self,
        target_id,
        api_schema_file_content: Dict,
        api_schema_file_content_format: APISchemaFileFormatEnum,
    ):
        url = PROBELY_API_TARGETS_UPLOAD_API_SCHEMA_FILE_URL.format(target_id=target_id)

        file_extension = api_schema_file_content_format.value

        if api_schema_file_content_format == APISchemaFileFormatEnum.YAML:
            file_content: str = yaml.dump(api_schema_file_content)
            file_content_type = "application/yaml"
        elif api_schema_file_content_format == APISchemaFileFormatEnum.JSON:
            file_content: str = json.dumps(api_schema_file_content)
            file_content_type = "application/json"

        file = BytesIO(file_content.encode("utf-8"))

        file_name = f"{target_id}-api_schema_file-{datetime.now()}.{file_extension}"
        files = {"file": (file_name, file, file_content_type)}

        resp_status_code, resp_content = ProbelyAPIClient.post(url=url, files=files)

        if resp_status_code != 201:
            raise ProbelyRequestFailed(resp_content)

        deserialized_data = self.model.serializer_class(**resp_content)
        return self.model(deserialized_data)

    def create(
        self,
        target_url: str,
        target_name: Union[str, None] = None,
        target_type: TargetTypeEnum = TargetTypeEnum.WEB,
        api_schema_type: Union[TargetAPISchemaTypeEnum, None] = None,
        api_schema_file_url: Union[str, None] = None,
        api_schema_file_content: dict = None,
        api_schema_file_content_format: APISchemaFileFormatEnum = None,
        extra_payload: Union[dict, None] = None,
    ) -> Target:
        """Creates new target

        :param api_schema_type:
        :type api_schema_type: APISchemaTypeEnum, optional.
        :param api_schema_file_url:
        :type api_schema_file_url: str, optional.
        :param api_schema_file_content:
        :type api_schema_file_content: dict, optional.
        :param target_type:
        :type target_type: TargetTypeEnum, optional.
        :param target_url: url to be scanned.
        :type target_url: str.
        :param target_name: name of target.
        :type target_name: str, optional.
        :param extra_payload: allows customization of request. Content should follow api request body
        :type extra_payload: Optional[dict].
        :raise: ProbelyBadRequest.
        :return: Created target content.

        """

        if api_schema_file_content and api_schema_file_url:
            raise ProbelyValidation(
                "Parameters 'api_schema_file_url' and 'api_schema_file_content' are mutually exclusive"
            )

        if target_type == TargetTypeEnum.API:
            if not api_schema_type:
                raise ProbelyValidation("API Targets require 'api_schema_type'")

            if not api_schema_file_url and not api_schema_file_content:
                raise ProbelyValidation(
                    "API Targets require 'api_schema_file_url' or 'api_schema_file_content'"
                )

            if api_schema_file_content:
                if api_schema_file_content_format is None or not isinstance(
                    api_schema_file_content_format, APISchemaFileFormatEnum
                ):
                    raise ProbelyValidation(
                        "Parameter 'api_schema_file_content' requires a valid 'api_schema_file_content_format'"
                    )

        query_params = {
            "duplicate_check": False,
            "skip_reachability_check": True,
        }

        body_data = {}
        if extra_payload:
            body_data = extra_payload

        arguments_settings = {
            "site": {"url": target_url},
            "type": target_type.api_request_value,
        }
        if target_name:
            arguments_settings["site"]["name"] = target_name

        if target_type == TargetTypeEnum.API:
            api_scan_settings = {}

            if api_schema_file_url:
                api_scan_settings["api_schema_url"] = api_schema_file_url

            if api_schema_type:
                api_scan_settings["api_schema_type"] = api_schema_type.api_request_value

            arguments_settings["site"]["api_scan_settings"] = api_scan_settings

        merge(body_data, arguments_settings, strategy=Strategy.REPLACE)

        resp_status_code, resp_content = ProbelyAPIClient.post(
            url=self.resource_url, query_params=query_params, payload=body_data
        )

        if resp_status_code == 400:
            raise ProbelyBadRequest(response_payload=resp_content)

        if resp_status_code != 201:
            raise ProbelyRequestFailed(resp_content)

        deserialized_data = self.model.serializer_class(**resp_content)
        target = self.model(deserialized_data)

        if api_schema_file_content:
            target = self._upload_api_schema_file(
                target.id,
                api_schema_file_content,
                api_schema_file_content_format,
            )

        return target

    def start_scan(
        self,
        target_or_id: Union[Target, str],
        extra_payload: Optional[Dict] = None,
    ) -> Scan:
        target_id = self._retrieve_id_from_entity_or_id(target_or_id)

        scan_target_url = PROBELY_API_TARGETS_START_SCAN_URL.format(target_id=target_id)

        resp_status_code, resp_content = ProbelyAPIClient.post(
            scan_target_url, payload=extra_payload
        )

        if resp_status_code == 400:
            raise ProbelyBadRequest(resp_content)
        if resp_status_code == 404:
            raise ProbelyObjectsNotFound(target_id)
        if resp_status_code != 200:
            raise ProbelyRequestFailed(resp_content)

        deserialized_data = Scan.serializer_class(**resp_content)
        return Scan(deserialized_data)

    def bulk_start_scan(
        self,
        targets_or_ids: List[Union[Target, str]],
        extra_payload: Optional[Dict] = None,
    ) -> List[Scan]:
        target_ids = self._retrieve_ids_from_entities_or_ids(targets_or_ids)

        extra_payload = extra_payload or {}

        payload = {
            "targets": [{"id": target_id} for target_id in target_ids],
            **extra_payload,
        }

        resp_status_code, resp_content = ProbelyAPIClient.post(
            PROBELY_API_SCANS_BULK_START_URL,
            query_params={ID_404_VALIDATION: True},
            payload=payload,
        )

        validate_id_404_response(status_code=resp_status_code, content=resp_content)
        if resp_status_code == 400:
            raise ProbelyBadRequest(resp_content)
        if resp_status_code != 200:
            raise ProbelyRequestFailed(resp_content)

        scans = [Scan.serializer_class(**scan_content) for scan_content in resp_content]
        scans = [Scan(scan) for scan in scans]
        return scans

    def bulk_schedule_scan(
        self,
        targets_or_ids: List[Union[Target, str]],
        date_time: datetime,
        timezone: str = None,
        recurrence: Optional[ScheduledScanRecurrenceEnum] = None,
        day_of_week: Optional[ScheduledScanDayOfWeekEnum] = None,
        week_of_month: Optional[ScheduledScanWeekOfMonthEnum] = None,
        scan_profile_id: Optional[str] = None,
        extra_payload: Optional[Dict] = None,
    ) -> List[ScheduledScan]:
        target_ids = self._retrieve_ids_from_entities_or_ids(targets_or_ids)

        if extra_payload:
            scheduledscan = {**extra_payload}
        else:
            scheduledscan = {}

        scheduledscan["date_time"] = date_time.isoformat()

        if recurrence:
            scheduledscan["recurrence"] = recurrence.api_request_value

        if timezone:
            scheduledscan["timezone"] = timezone

        if scan_profile_id:
            scheduledscan["scan_profile"] = scan_profile_id

        if day_of_week or week_of_month:
            if not day_of_week or not week_of_month:
                raise ProbelyValidation(
                    "'day of week' and 'week of month' are required"
                )

            if recurrence not in (
                ScheduledScanRecurrenceEnum.MONTHLY,
                ScheduledScanRecurrenceEnum.QUARTERLY,
            ):
                raise ProbelyValidation(
                    "'day of week' and 'week of month' require monthly or quarterly 'recurrence'"
                )
            scheduledscan["run_on_day_of_week"] = True
            scheduledscan["scheduled_day_of_week"] = day_of_week.api_request_value
            scheduledscan["week_index"] = week_of_month.api_request_value

        ids_dict = [{"id": target_id} for target_id in target_ids]
        request_payload = {
            "targets": ids_dict,
            "scheduledscan": scheduledscan,
        }

        resp_status_code, resp_content = ProbelyAPIClient.post(
            PROBELY_API_SCHEDULED_SCANS_BULK_CREATE_URL,
            payload=request_payload,
        )

        if resp_status_code == 400:
            raise ProbelyBadRequest(resp_content)
        if resp_status_code != 201:
            raise ProbelyRequestFailed(resp_content)

        scheduled_scans_content = [
            ScheduledScan.serializer_class(**content) for content in resp_content
        ]
        scheduled_scans = [ScheduledScan(s_scan) for s_scan in scheduled_scans_content]
        return scheduled_scans

    def add_sequence(
        self,
        target_or_id: Union[Target, str],
        name: Union[str, None],
        sequence_steps: List[Dict],
        sequence_type: Union[SequenceTypeEnum, None] = None,
        requires_authentication: Union[bool, None] = None,
        enabled: Union[str, None] = None,
        index: Union[int, None] = None,
        extra_payload: Union[Dict, None] = None,
    ) -> TargetSequence:
        """Creates new Sequence

        :param target_or_id:
        :param name :
        :type name: str.
        :param sequence_steps :
        :type sequence_steps: list.
        :param sequence_type:
        :type sequence_type: SequenceTypeEnum, optional.
        :param requires_authentication:
        :type requires_authentication: bool, optional.
        :param enabled: Enabled.
        :type enabled: bool, optional.
        :param index:
        :type index: int, optional.
        :param extra_payload: allows customization of request. Content should follow api request body
        :type extra_payload: Optional[Dict].
        :raise: ProbelyBadRequest.
        :return: Created Sequence instance.
        """

        target_id = self._retrieve_id_from_entity_or_id(target_or_id)
        query_params = {"include": ["content", "target"]}

        body_data = {}
        if extra_payload:
            body_data = extra_payload

        content = json.dumps(sequence_steps)

        passed_values = {
            "name": name,
            "content": content,
            "type": sequence_type.api_request_value if sequence_type else None,
            "requires_authentication": requires_authentication,
            "enabled": enabled,
            "index": index,
        }
        passed_values = {k: v for k, v in passed_values.items() if v is not None}

        merge(body_data, passed_values, strategy=Strategy.REPLACE)

        url = PROBELY_API_SEQUENCES_URL.format(target_id=target_id)
        resp_status_code, resp_content = ProbelyAPIClient.post(
            url=url, query_params=query_params, payload=body_data
        )

        if resp_status_code == 400:
            raise ProbelyBadRequest(response_payload=resp_content)

        if resp_status_code != 201:
            raise ProbelyRequestFailed(resp_content)

        deserialized_data = TargetSequence.serializer_class(**resp_content)
        return TargetSequence(deserialized_data)

    def add_extra_host(
        self,
        target_or_id: Union[Target, str],
        host: Optional[str] = None,
        include: Optional[bool] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        skip_reachability_check: Optional[bool] = False,
        headers: Optional[List[Dict]] = None,
        cookies: Optional[List[Dict]] = None,
        extra_payload: Optional[Dict] = None,
    ) -> TargetExtraHost:
        """
        Create a new Extra Host for a Target.

        :param target_or_id: The target ID.
        :type target_or_id: Union[Target, str]
        :param host: The host to be added.
        :type host: str, optional.
        :param include: Whether to include the host in the scan.
        :type include: bool, optional.
        :param name: The name of the Extra Host.
        :type name: str, optional.
        :param description:The description of the Extra Host.
        :type description: str, optional.
        :param skip_reachability_check:
        :type skip_reachability_check: bool
        :param headers: Custom headers to be sent.
        :type headers: List[Dict], optional.
        :param cookies: Custom cookies to be sent.
        :type cookies: List[Dict], optional.
        :param extra_payload: Allows customization of request. Content should follow api request body.
        :type extra_payload: Optional[Dict].
        :raise: ProbelyBadRequest.
        :return: Created Extra Host instance.
        """
        target_id = self._retrieve_id_from_entity_or_id(target_or_id)

        body_data = extra_payload if extra_payload else {}

        # Update body_data with explicitly passed arguments, overriding extra_payload if necessary
        passed_values = {
            "host": host,
            "include": include,
            "name": name,
            "desc": description,
            "headers": headers,
            "cookies": cookies,
        }
        passed_values = {k: v for k, v in passed_values.items() if v is not None}

        # Merge passed_values into body_data
        body_data.update(passed_values)

        query_params = {
            "skip_reachability_check": skip_reachability_check,
            "include": ["target"],
        }

        url = PROBELY_API_EXTRA_HOSTS_URL.format(target_id=target_id)
        resp_status_code, resp_content = ProbelyAPIClient.post(
            url=url, query_params=query_params, payload=body_data
        )

        if resp_status_code == 400:
            raise ProbelyBadRequest(response_payload=resp_content)

        if resp_status_code != 201:
            raise ProbelyRequestFailed(resp_content)

        deserialized_data = TargetExtraHost.serializer_class(**resp_content)
        return TargetExtraHost(deserialized_data)
