from typing import Generator, Optional

from typing import List, Union, Dict

from probely.exceptions import ProbelyException, ProbelyBadRequest, ProbelyRequestFailed
from probely.sdk.enums import SelfReviewStatusEnum
from probely.sdk.managers.common import SdkBaseManager
from probely.settings import (
    PROBELY_API_FINDINGS_DETAIL_URL,
    PROBELY_API_FINDINGS_URL,
    PROBELY_API_FINDINGS_BULK_RETEST_URL,
    PROBELY_API_FINDINGS_BULK_UPDATE,
)
from probely.sdk.models import Finding
from probely.sdk.managers.mixins.list import ListMixin
from probely.sdk.managers.mixins.retrieve import RetrieveByIDMixin
from probely.sdk.managers.mixins.retrieve_multiple import RetrieveMultipleMixin
from probely.sdk.client import ProbelyAPIClient


def _retrieve_findings_compound_ids_or_str_ids(
    findings: List[Union[Finding, str]],
) -> List[str]:
    findings_compound_ids = []

    for finding in findings:
        if isinstance(finding, Finding):
            finding_compound_id = "{target_id}-{finding_id}".format(
                target_id=str(finding.target.id),
                finding_id=str(finding.id),
            )
            findings_compound_ids.append(finding_compound_id)
        elif isinstance(finding, str):
            findings_compound_ids.append(finding)
        else:
            raise ProbelyException(
                f"Invalid type, argument '{str(finding)}'. Must be Finding or str"
            )

    return findings_compound_ids


def _retrieve_retestable_ids(findings_compound_ids: List[str]) -> List[Dict]:
    retestable_ids = []
    for compound_id in findings_compound_ids:
        target_id, finding_id = compound_id.split("-")
        retestable_ids.append({"target_id": target_id, "finding_id": finding_id})

    return retestable_ids


def _build_compound_ids(findings_dicts: List[Dict]) -> List[str]:
    compound_ids = []
    for finding_dict in findings_dicts:
        compound_id = "{target_id}-{finding_id}".format(
            target_id=str(finding_dict["target_id"]),
            finding_id=str(finding_dict["finding_id"]),
        )
        compound_ids.append(compound_id)

    return compound_ids


class FindingManager(
    RetrieveByIDMixin, RetrieveMultipleMixin, ListMixin, SdkBaseManager
):
    resource_url = PROBELY_API_FINDINGS_URL
    resource_detail_url = PROBELY_API_FINDINGS_DETAIL_URL
    listing_ordering = "-last_found"
    model = Finding

    def list(self, filters: Optional[Dict] = None) -> Generator[Finding, None, None]:
        # TODO: add accepted filter
        return self._list(filters=filters, ordering=self.listing_ordering)

    def retrieve_multiple(
        self, findings_or_id: List[Union[Finding, str]]
    ) -> Generator[Finding, None, None]:
        return self._retrieve_multiple(findings_or_id)

    def retrieve(self, finding_or_id: Union[Finding, str]) -> Finding:
        return self._retrieve_by_id(finding_or_id)

    def bulk_retest(
        self,
        findings_or_ids: List[Union[Finding, str]],
        ignore_blackout_period: Union[bool, None] = None,
        scan_profile: Union[str, None] = None,
        extra_payload: Dict = None,
    ) -> Generator[Finding, None, None]:
        findings_compound_ids = _retrieve_findings_compound_ids_or_str_ids(
            findings_or_ids
        )

        payload = {
            "ids": _retrieve_retestable_ids(findings_compound_ids),
        }
        if extra_payload:
            payload.update(extra_payload)

        if ignore_blackout_period is not None:
            payload["ignore_blackout_period"] = ignore_blackout_period

        if scan_profile:
            payload["scan_profile"] = scan_profile

        resp_status_code, resp_content = ProbelyAPIClient.post(
            url=PROBELY_API_FINDINGS_BULK_RETEST_URL,
            payload=payload,
        )

        if resp_status_code == 400:
            raise ProbelyBadRequest(resp_content)

        if resp_status_code != 200:
            raise ProbelyRequestFailed(resp_content)

        retested_findings_ids = _build_compound_ids(resp_content["ids"])

        findings = self.retrieve_multiple(retested_findings_ids)

        return findings

    def bulk_self_review(
        self,
        findings_or_ids: List[Union[Finding, str]],
        review_status: SelfReviewStatusEnum,
        justification: str = "",
        extra_payload: Dict = None,
    ) -> Generator[Finding, None, None]:
        findings_compound_ids = _retrieve_findings_compound_ids_or_str_ids(
            findings_or_ids
        )

        payload = {
            "ids": _retrieve_retestable_ids(findings_compound_ids),
            "review_status": review_status.api_request_value,
        }
        if justification:
            payload["review_reason"] = justification
        if extra_payload:
            payload = {**extra_payload, **payload}

        resp_status_code, resp_content = ProbelyAPIClient.post(
            url=PROBELY_API_FINDINGS_BULK_UPDATE,
            payload=payload,
        )

        if resp_status_code == 400:
            raise ProbelyBadRequest(resp_content)

        if resp_status_code != 200:
            raise ProbelyRequestFailed(resp_content)

        self_reviewed_findings_ids = _build_compound_ids(resp_content["ids"])

        findings = self.retrieve_multiple(self_reviewed_findings_ids)

        return findings
