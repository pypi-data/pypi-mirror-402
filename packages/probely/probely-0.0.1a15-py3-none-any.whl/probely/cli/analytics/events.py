from argparse import Namespace

from probely.cli.analytics import events_logger
from probely.cli.analytics.schemas import (
    AnalyticsStarScanArgumentsSchema,
    AnalyticsTargetsFiltersSchema,
    AnalyticsFollowScanArgumentsSchema,
)
from probely.cli.analytics.client import send_analytics_event
from probely.cli.enums import AnalyticsEventsEnum


def start_scan_used_analytics_event(args: Namespace, targets_count):
    try:
        event_data = {
            "targets_count": targets_count,
            "filters": AnalyticsTargetsFiltersSchema().load(vars(args)),
            "arguments": AnalyticsStarScanArgumentsSchema().load(vars(args)),
        }

        send_analytics_event(AnalyticsEventsEnum.START_SCAN_USED, event_data)
    except Exception as e:
        events_logger.debug(f"start_scan_used_analytics_event failed: {e}")


def follow_scan_used_analytics_event(args: Namespace, targets_count):
    try:
        event_data = {
            "targets_count": targets_count,
            "arguments": AnalyticsFollowScanArgumentsSchema().load(vars(args)),
        }

        send_analytics_event(AnalyticsEventsEnum.FOLLOW_SCAN_USED, event_data)
    except Exception as e:
        events_logger.debug(f"follow_scan_used_analytics_event failed: {e}")
