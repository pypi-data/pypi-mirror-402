import importlib
from abc import ABC, abstractmethod
from typing import Type, TypeVar

from pydantic import BaseModel

from probely.sdk.schemas import (
    TargetExtraHostDataModel,
    FindingDataModel,
    ScanDataModel,
    TargetSequenceDataModel,
    TargetDataModel,
    TargetLabelDataModel,
    ScanProfileDataModel,
    ScheduledScanDataModel,
)


class SDKModel(ABC):
    """
    Base class for all resource models, providing common serialization methods.
    """

    manager = None  # To be assigned in __init__ (circular import workaround)

    @abstractmethod
    def serializer_class(self) -> Type[BaseModel]:
        pass

    @property
    @abstractmethod
    def manager_class_str(self) -> str:
        pass

    def __init__(self, data_model):
        self._data = data_model

        if not self.__class__.manager and self.manager_class_str:
            module_name, class_name = self.manager_class_str.rsplit(".", 1)
            manager_class = getattr(importlib.import_module(module_name), class_name)
            self.__class__.manager = manager_class()

    def __getattr__(self, name):
        return getattr(self._data, name)

    def to_dict(self, *args, **kwargs) -> dict:
        """
        Serialize the object to a dictionary.
        """
        return self._data.model_dump(*args, **kwargs)

    def to_json(self, *args, **kwargs) -> str:
        """
        Serialize the object to a JSON string.
        """
        return self.model_dump_json(*args, **kwargs)


SDKModelType = TypeVar("SDKModelType", bound=SDKModel)


class Finding(SDKModel):
    serializer_class = FindingDataModel
    manager_class_str = "probely.sdk.managers.FindingManager"


class Target(SDKModel):
    serializer_class = TargetDataModel
    manager_class_str = "probely.sdk.managers.TargetManager"

    def start_scan(self):
        return self.manager.start_scan(self)


class TargetLabel(SDKModel):
    serializer_class = TargetLabelDataModel
    manager_class_str = "probely.sdk.managers.TargetLabelManager"


class Scan(SDKModel):
    serializer_class = ScanDataModel
    manager_class_str = "probely.sdk.managers.ScanManager"

    def cancel(self):
        return self.manager.cancel(self)

    def pause(self):
        return self.manager.pause(self)

    def resume(self, ignore_blackout_period: bool = False):
        return self.manager.resume(self, ignore_blackout_period=ignore_blackout_period)


class TargetSequence(SDKModel):
    serializer_class = TargetSequenceDataModel
    manager_class_str = "probely.sdk.managers.TargetSequenceManager"


class TargetExtraHost(SDKModel):
    serializer_class = TargetExtraHostDataModel
    manager_class_str = "probely.sdk.managers.TargetExtraHostManager"


class ScanProfile(SDKModel):
    serializer_class = ScanProfileDataModel
    manager_class_str = "probely.sdk.managers.ScanProfileManager"


class ScheduledScan(SDKModel):
    serializer_class = ScheduledScanDataModel
    manager_class_str = "probely.sdk.managers.ScheduledScanManager"
