from probely.sdk.enums import ProbelyCLIEnum


class OutputEnum(ProbelyCLIEnum):
    YAML = "yaml"
    JSON = "json"
    TABLE = "table"
    IDS_ONLY = "ids_only"


class AnalyticsEventsEnum(ProbelyCLIEnum):
    START_SCAN_USED = "cli_start_scan_used"
    FOLLOW_SCAN_USED = "cli_follow_scan_used"


class CLIAnalyticsCICDProviderEnum(ProbelyCLIEnum):
    GITHUB_ACTIONS = "github_actions"
    GITLAB_CICD = "gitlab_cicd"
    AZURE_DEVOPS = "azure_devops"
    JENKINS = "jenkins"
    LOCAL_OR_UNKNOWN_OR_OTHER = "local_or_unknown_or_other"
