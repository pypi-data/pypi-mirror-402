from enum import Enum
from typing import List


class ProbelyCLIEnum(Enum):
    def __init__(self, api_response_value, api_filter_value=None):
        self._value_ = api_response_value
        self._api_filter_value = api_filter_value or api_response_value

    @property
    def api_filter_value(self):
        return self._api_filter_value

    @property
    def api_response_value(self):
        return self.value

    @property
    def api_request_value(self):
        return self.value

    @property
    def cli_choice(self):
        return self.name

    @classmethod
    def get_by_api_response_value(cls, value):
        for enum_element in cls:
            if enum_element.value == value:
                return enum_element

        raise ValueError("{} is not a valid {}".format(value, cls.__name__))

    @classmethod
    def get_by_api_filter_value(cls, api_filter_value):
        for enum_element in cls:
            if enum_element._api_filter_value == api_filter_value:
                return enum_element

        raise ValueError("{} is not a valid {}".format(api_filter_value, cls.__name__))

    @classmethod
    def all_names(cls):
        names = [enum_element.name for enum_element in cls]
        return names

    @classmethod
    def cli_input_choices(cls):
        return cls.all_names()


class TargetRiskEnum(ProbelyCLIEnum):
    NA = (None, "null")
    NO_RISK = (0, "0")
    LOW = (10, "10")
    MEDIUM = (20, "20")
    HIGH = (30, "30")
    CRITICAL = (40, "40")


class TargetTypeEnum(ProbelyCLIEnum):
    WEB = "single"
    API = "api"


class ScanProfileTargetTypeEnum(ProbelyCLIEnum):
    WEB = "web"
    API = "api"


class TargetAPISchemaTypeEnum(ProbelyCLIEnum):
    OPENAPI = "openapi"
    POSTMAN = "postman"


class APISchemaFileFormatEnum(ProbelyCLIEnum):
    JSON = "json"
    YAML = "yaml"


class ScheduledScanRecurrenceEnum(ProbelyCLIEnum):
    NEVER = ""
    HOURLY = "h"
    DAILY = "d"
    WEEKLY = "w"
    MONTHLY = "m"
    QUARTERLY = "q"


class ScheduledScanDayOfWeekEnum(ProbelyCLIEnum):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7


class ScheduledScanWeekOfMonthEnum(ProbelyCLIEnum):
    FIRST = "first"
    SECOND = "second"
    THIRD = "third"
    FOURTH = "fourth"
    LAST = "last"


class FindingSeverityEnum(ProbelyCLIEnum):
    LOW = (TargetRiskEnum.LOW.value, TargetRiskEnum.LOW.api_filter_value)
    MEDIUM = (TargetRiskEnum.MEDIUM.value, TargetRiskEnum.MEDIUM.api_filter_value)
    HIGH = (TargetRiskEnum.HIGH.value, TargetRiskEnum.HIGH.api_filter_value)
    CRITICAL = (TargetRiskEnum.CRITICAL.value, TargetRiskEnum.CRITICAL.api_filter_value)

    @classmethod
    def ordered_severities(cls) -> List["FindingSeverityEnum"]:
        return [
            cls.LOW,
            cls.MEDIUM,
            cls.HIGH,
            cls.CRITICAL,
        ]

    @classmethod
    def get_severities_on_threshold(cls, severity: "FindingSeverityEnum"):
        severity_hierarch: List[cls] = cls.ordered_severities()

        severity_threshold_index = severity_hierarch.index(severity)
        severity_threshold = severity_hierarch[severity_threshold_index:]

        return severity_threshold


class FindingStateEnum(ProbelyCLIEnum):
    FIXED = "fixed"
    NOT_FIXED = "notfixed"
    ACCEPTED = "accepted"
    RETESTING = "retesting"


class ScanStatusEnum(ProbelyCLIEnum):
    CANCELED = "canceled"
    CANCELING = "canceling"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    PAUSING = "pausing"
    QUEUED = "queued"
    RESUMING = "resuming"
    STARTED = "started"
    UNDER_REVIEW = "under_review"
    FINISHING_UP = "finishing_up"

    @classmethod
    def interrupted_status(cls) -> List["ScanStatusEnum"]:
        return [
            cls.PAUSED,
            cls.FAILED,
            cls.CANCELED,
        ]


class LogicalOperatorTypeEnum(ProbelyCLIEnum):
    AND = "and"
    OR = "or"


class SequenceTypeEnum(ProbelyCLIEnum):
    LOGIN = "login"
    NAVIGATION = "navigation"


class SelfReviewStatusEnum(ProbelyCLIEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
