from typing import Dict, List, Union, Generator, Optional

from probely.sdk.managers.common import SdkBaseManager
from probely.sdk.managers.mixins.delete import ParentedDeleteMixin
from probely.settings import (
    PROBELY_API_SEQUENCES_DETAIL_URL,
    PROBELY_API_ACCOUNT_SEQUENCES_URL,
)
from probely.sdk.models import TargetSequence
from probely.sdk.managers.mixins.list import ListMixin
from probely.sdk.managers.mixins.update import ParentedUpdateMixin
from probely.sdk.managers.mixins.retrieve_multiple import RetrieveMultipleMixin


class TargetSequenceManager(
    RetrieveMultipleMixin,
    ListMixin,
    ParentedUpdateMixin,
    ParentedDeleteMixin,
    SdkBaseManager,
):
    default_query_params = {"include": ["content", "target"]}
    resource_url = PROBELY_API_ACCOUNT_SEQUENCES_URL
    resource_detail_url = PROBELY_API_SEQUENCES_DETAIL_URL  # TODO: Remove?
    parented_resource_detail_url = PROBELY_API_SEQUENCES_DETAIL_URL
    model = TargetSequence

    def list(
        self, filters: Optional[Dict] = None
    ) -> Generator[TargetSequence, None, None]:
        return self._list(filters=filters)

    def retrieve_multiple(
        self,
        target_sequences_or_ids: List[Union[TargetSequence, str]],
    ) -> Generator[TargetSequence, None, None]:
        return self._retrieve_multiple(target_sequences_or_ids)

    def retrieve(
        self,
        target_sequence_or_id: Union[TargetSequence, str],
    ) -> TargetSequence:
        target_sequence_id = self._retrieve_id_from_entity_or_id(target_sequence_or_id)

        target_sequence: TargetSequence = list(
            self.retrieve_multiple([target_sequence_id])
        )[0]

        return target_sequence

    def update(
        self,
        target_sequence_or_id: Union[TargetSequence, str],
        payload: Dict,
    ) -> TargetSequence:
        if isinstance(target_sequence_or_id, TargetSequence):
            sequence = target_sequence_or_id
        else:
            sequence = self.retrieve(target_sequence_or_id)

        updated_target_sequence = self._parented_update(
            target_id=sequence.target.id,
            entity_id=sequence.id,
            payload=payload,
        )

        return updated_target_sequence

    def delete(self, target_sequence_or_id: Union[TargetSequence, str]) -> None:
        if isinstance(target_sequence_or_id, TargetSequence):
            sequence = target_sequence_or_id
        else:
            sequence = self.retrieve(target_sequence_or_id)

        super()._parented_delete(target_id=sequence.target.id, entity_id=sequence.id)
