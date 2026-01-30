import os
from threading import Thread
from typing import Dict

from probely.settings import PROBELY_DISABLE_ANALYTICS
from probely.cli.analytics import events_logger
from probely.cli.enums import CLIAnalyticsCICDProviderEnum, AnalyticsEventsEnum
from probely.sdk.client import ProbelyAPIClient
from probely.settings import PROBELY_API_ANALYTICS_EVENT_URL, RUNNING_PYTHON_VERSION
from probely.version import __version__


def get_cicd_provider():
    detection_env_var_mapper = {
        # https://docs.github.com/en/actions/reference/workflows-and-actions/variables#default-environment-variables
        CLIAnalyticsCICDProviderEnum.GITHUB_ACTIONS: "GITHUB_ACTIONS",  # always True
        # https://docs.gitlab.com/ci/variables/predefined_variables/#predefined-variables
        CLIAnalyticsCICDProviderEnum.GITLAB_CICD: "GITLAB_CI",  # always True
        # https://learn.microsoft.com/en-us/azure/devops/pipelines/build/variables#system-variables
        CLIAnalyticsCICDProviderEnum.AZURE_DEVOPS: "TF_BUILD",  # always True
        # https://www.jenkins.io/doc/book/pipeline/jenkinsfile/#using-environment-variables
        CLIAnalyticsCICDProviderEnum.JENKINS: "JENKINS_URL",
    }

    for cicd_provider, detection_env_var in detection_env_var_mapper.items():
        if detection_env_var in os.environ:
            return cicd_provider
    else:
        return CLIAnalyticsCICDProviderEnum.LOCAL_OR_UNKNOWN_OR_OTHER


def _send_analytics_event_async(analytics_event_data: Dict):
    response = ProbelyAPIClient.post(
        PROBELY_API_ANALYTICS_EVENT_URL,
        payload=analytics_event_data,
    )
    events_logger.debug("Event sent: %s", response)


def send_analytics_event(event: AnalyticsEventsEnum, event_data: Dict):
    if PROBELY_DISABLE_ANALYTICS:
        events_logger.debug("Events are disabled")
        return

    python_version_major_minor_only = ".".join(RUNNING_PYTHON_VERSION.split(".")[:2])
    cicd_provider: CLIAnalyticsCICDProviderEnum = get_cicd_provider()

    analytics_event_data = {
        "event_name": event.value,
        "cli_version": __version__,
        "python_version": python_version_major_minor_only,
        "cicd_provider": cicd_provider.value,
        "event_data": event_data,
    }

    events_logger.debug("Sending Event: payload %s", analytics_event_data)

    def exception_safe_wrapper(func, *args):
        try:
            func(*args)
        except Exception as e:
            events_logger.debug(f"Failed to send Event: {e}")

    thread = Thread(
        target=exception_safe_wrapper,
        args=(_send_analytics_event_async, analytics_event_data),
        daemon=True,  # does not block the main thread
    )
    thread.start()

    thread.join(timeout=0.5)
