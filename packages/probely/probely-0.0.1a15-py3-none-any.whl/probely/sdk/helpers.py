from typing import List, Sequence, Type, Union

from probely.constants import ID_404_VALIDATION
from probely.exceptions import (
    ProbelyObjectsNotFound,
    ProbelyException,
)
from probely.sdk.models import SDKModel, Scan
from probely.settings import PROBELY_UI_SCAN_DETAILS_URL


def validate_id_404_response(status_code: int, content: dict):
    """
    Validates Custom API response that is triggered by 'is_id_404_validation' flag.
    It expects following response:
    {
        "detail": "Not Found",
        "is_id_404_validation": true,
        "invalid_ids": [
            "9vebyEVLNoZX",
            "6CuzJtJmMp48"
        ]
    }

    It's specific for this content and shouldn't replace other 404 validations
    """
    if status_code == 404:
        if content.get(ID_404_VALIDATION):
            raise ProbelyObjectsNotFound(content["invalid_ids"])


# Deprecated: Check base manager
def retrieve_id_from_entity_or_str(
    entity_class: Type[SDKModel],
    entity: Union[SDKModel, str],
) -> str:
    if isinstance(entity, entity_class):
        return str(entity.id)
    elif isinstance(entity, str):
        return entity
    else:
        raise ProbelyException(
            f"Invalid type, argument '{str(entity)}'. Must be {entity_class} or str"
        )


# Deprecated: Check base manager
def list_ids_or_entity_ids(
    entity_class: Type[SDKModel],
    entities: Sequence[Union[SDKModel, str]],
) -> List[str]:
    entity_ids = []
    for entity in entities:
        entity_id: str = retrieve_id_from_entity_or_str(entity_class, entity)
        entity_ids.append(entity_id)

    return entity_ids


def build_scan_details_url(scan: Scan) -> str:
    scan_details_url = PROBELY_UI_SCAN_DETAILS_URL.format(
        target_id=scan.target.id, id=scan.id
    )
    return scan_details_url
