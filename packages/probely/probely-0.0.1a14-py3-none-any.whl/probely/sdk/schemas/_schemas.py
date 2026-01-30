from __future__ import annotations

from datetime import time
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from uuid import UUID

from pydantic import AnyUrl, AwareDatetime, BaseModel, EmailStr, Field
from typing_extensions import Annotated


class CookieHeader(BaseModel):
    name: str
    value: str
    allow_testing: bool
    authentication: bool


class NameValue(BaseModel):
    name: str
    value: str


class Severity(int, Enum):
    low = 10
    medium = 20
    high = 30
    critical = 40


class ReportType(Enum):
    default = "default"
    executive_summary = "executive_summary"
    owasp = "owasp"
    pci = "pci"
    pci4 = "pci4"
    iso27001 = "iso27001"
    hipaa = "hipaa"


class OtpDigits(int, Enum):
    six = 6
    seven = 7
    eight = 8


class OtpAlgorithm(str, Enum):
    SHA1 = "SHA1"
    SHA256 = "SHA256"
    SHA512 = "SHA512"


class OTPTypes(str, Enum):
    TOTP = "totp"
    OTHER = "other"


class MediaType(str, Enum):
    application_json = "application/json"
    application_x_www_form_urlencoded = "application/x-www-form-urlencoded"


class VerificationMethod(str, Enum):
    file = "file"
    back_office = "back_office"
    existing_domain = "existing_domain"
    dns_txt = "dns_txt"
    dns = "dns"
    dns_cname = "dns_cname"
    meta_tag = "meta_tag"
    whitelist = "whitelist"
    email = "email"
    aws_route53 = "aws_route53"
    cloudflare = "cloudflare"
    waved = "waved"


class FindingState(str, Enum):
    notfixed = "notfixed"
    invalid = "invalid"
    accepted = "accepted"
    fixed = "fixed"
    none = ""


class InsertionPoint(str, Enum):
    cookie = "cookie"
    parameter = "parameter"
    arbitrary_url_param = "arbitrary_url_param"
    header = "header"
    url_folder = "url_folder"
    url_filename = "url_filename"
    json_parameter = "json_parameter"
    request_body = "request_body"
    multipart_parameter = "multipart_parameter"
    graphql_parameter = "graphql_parameter"
    non_standard_parameter = "non_standard_parameter"
    field_ = ""


class LogoutCondition(str, Enum):
    any = "any"
    all = "all"


class BasicAuth(BaseModel):
    username: Annotated[str, Field(max_length=255)]
    password: Annotated[str, Field(max_length=255)]


class TargetTypeEnum(str, Enum):
    api = "api"
    web = "single"


class ReportFileformat(str, Enum):
    pdf = "pdf"
    docx = "docx"


class ApiSchemaType(str, Enum):
    openapi = "openapi"
    postman = "postman"


class TokenParameterLocation(str, Enum):
    cookie = "cookie"
    header = "header"


class RequestResponsePairMarkdown(BaseModel):
    request: str
    response: str


class Method(str, Enum):
    get = "get"
    post = "post"
    delete = "delete"
    put = "put"
    patch = "patch"
    head = "head"
    trace = "trace"
    options = "options"
    debug = "debug"
    track = "track"
    dns = "dns"
    dns_soa = "dns_soa"
    dns_a = "dns_a"
    dns_aaaa = "dns_aaaa"
    dns_cname = "dns_cname"


class Recurrence(Enum):
    h = "h"  # hourly
    d = "d"  # daily
    w = "w"  # weekly
    m = "m"  # monthly
    q = "q"  # quarterly
    none = ""  # no recurrence


class DayOfWeek(Enum):
    integer_1 = 1
    integer_2 = 2
    integer_3 = 3
    integer_4 = 4
    integer_5 = 5
    integer_6 = 6
    integer_7 = 7


class WeekIndex(Enum):
    first = "first"
    second = "second"
    third = "third"
    fourth = "fourth"
    last = "last"
    none = ""


class Framework(BaseModel):
    id: Annotated[
        str, Field(description="A unique Base58 value identifying this object.")
    ]
    name: Annotated[
        str,
        Field(
            description=(
                'Name of the technology.  For example, "PHP, "SQLite", "Python",'
                ' "Apache", or "Wordpress".  The maximum length is 255 characters.'
            ),
            max_length=255,
            title="Framework Name",
        ),
    ]
    desc: Annotated[
        str,
        Field(
            description='Description of the technology.  Defaults to "".',
            title="Framework Description",
        ),
    ]


class APIScanSettings(BaseModel):
    api_schema_type: Annotated[
        ApiSchemaType,
        Field(description="Type of schema that defines the API."),
    ] = ApiSchemaType.openapi
    api_schema_url: Annotated[
        Optional[AnyUrl],
        Field(
            description="URL to retrieve the API schema from.",
        ),
    ] = None
    api_schema_file: Optional[str] = None
    custom_api_parameters: Annotated[
        List[NameValue], Field(description="Custom values for certain API parameters.")
    ]
    media_type: Annotated[
        MediaType,
        Field(description="Format of the payload."),
    ] = MediaType.application_json
    api_login_url: Annotated[
        Union[AnyUrl, Literal[""]],
        Field(
            description=("URL to make the authentication request to the API."),
        ),
    ]
    api_login_payload: Annotated[
        str,
        Field(
            description=("Payload to send in the authentication request."),
            max_length=4096,
        ),
    ]
    api_login_enabled: bool = False
    api_login_token_field: Annotated[
        str,
        Field(
            description=(
                "Field containing the authentication token in the response to the"
                " authentication request."
            ),
            max_length=256,
        ),
    ]
    token_prefix: Annotated[
        str,
        Field(
            description=(
                "Prefix to add to the authentication token. "
                "For example, Bearer or JWT."
            ),
            max_length=16,
        ),
    ]
    token_parameter_name: Annotated[
        str,
        Field(
            description=(
                "Parameter name to send the authentication token. "
                "For example, `Authorization`."
            ),
            max_length=256,
        ),
    ]
    token_parameter_location: Annotated[
        Union[TokenParameterLocation, Literal[""]],
        Field(
            description=(
                "Where to send the parameter name with the authentication token and the prefix."
            )
        ),
    ]


class SimpleUser(BaseModel):
    id: Annotated[
        str, Field(description="A unique Base58 value identifying this object.")
    ]
    email: Annotated[
        Union[EmailStr, Literal[""]],
        Field(description="Email of the user.", max_length=254, title="Email address"),
    ] = None
    name: Annotated[str, Field(description="Name of the user.", max_length=60)]


class ScopeLabel(BaseModel):
    id: Annotated[
        str, Field(description="A unique Base58 value identifying this object.")
    ]
    name: Annotated[
        str,
        Field(
            description="Name of the label. The maximum length is 255 characters.",
            max_length=255,
        ),
    ]
    color: Annotated[
        str,
        Field(
            description="Color of the label",
            pattern="^[a-zA-Z0-9#_-]*$",
        ),
    ]
    changed_by: Annotated[SimpleUser, Field(description="User who last made changes.")]
    changed: Annotated[
        AwareDatetime,
        Field(
            description=(
                "Date and time of the last change, in ISO 8601 UTC format.  For"
                ' example, "2023-08-09T13:27.43.8208302".'
            )
        ),
    ]


class FindingLabel(ScopeLabel):
    pass


class BlackoutPeriod(BaseModel):
    begin: Annotated[
        time,
        Field(
            description=(
                "Time of when the blackout period starts, in ISO 8601 UTC format. "
                ' For example, "13:27".'
            )
        ),
    ]
    cease: Annotated[
        time,
        Field(
            description=(
                "Time of when the blackout period ceases, in ISO 8601 UTC format. "
                ' For example, "13:27".'
            )
        ),
    ]
    weekdays: List[int]
    enabled: Annotated[
        bool,
        Field(description="If true, the blackout period is enabled."),
    ]
    timezone: Annotated[str, Field(max_length=64)] = "UTC"
    changed: Annotated[
        AwareDatetime,
        Field(
            description=(
                "Date and time of the last change, in ISO 8601 UTC format.  For"
                ' example, "2023-08-09T13:27.43.8208302".'
            )
        ),
    ]
    changed_by: Annotated[SimpleUser, Field(description="User who last made changes.")]


class SimpleVulnerabilityDefinition(BaseModel):
    id: str
    name: Annotated[
        str,
        Field(
            description=("Name of the vulnerability."),
            max_length=255,
        ),
    ]
    desc: Annotated[str, Field(description="Description of the vulnerability.")]


class ScanningAgent(BaseModel):
    id: str
    name: Annotated[str, Field(max_length=255)]
    installer_generated: bool
    online: bool
    fallback: bool
    rx_bytes: int
    tx_bytes: int
    latest_handshake: Optional[int] = None


class SimpleTeam(BaseModel):
    id: Annotated[
        str,
        Field(description="A unique Base58 value identifying this object."),
    ]
    name: Annotated[str, Field(max_length=255)]


class TargetBase(BaseModel):
    id: Annotated[
        str, Field(description="A unique Base58 value identifying this object.")
    ]
    name: Annotated[
        str,
        Field(
            description=("Name of the Target or extra host."),
            max_length=255,
        ),
    ]
    desc: Annotated[str, Field(description="Description of the Target.")]
    url: Annotated[AnyUrl, Field(description="URL of the Target.")]
    host: Annotated[str, Field(description="Hostname of the Target.")]
    has_form_login: Annotated[
        bool,
        Field(
            description=(
                "If true, the Target authentication is done through a login form."
            )
        ),
    ] = False
    form_login_url: Annotated[
        Union[AnyUrl, Literal[""]],
        Field(description="URL of the login form of the Target."),
    ]
    form_login_check_pattern: Annotated[
        str,
        Field(
            description=("Pattern to check a successful login."),
            max_length=255,
        ),
    ]
    form_login: Annotated[
        Optional[List[NameValue]],
        Field(description="Field and value pairs to fill the login form."),
    ] = None
    logout_detection_enabled: Annotated[
        bool,
        Field(
            description=(
                "If true, detects any undesired logouts that may occur during scans"
                " to log back in. "
                "Requires `check_session_url` and `logout_detectors` to be defined."
            )
        ),
    ] = False
    has_sequence_login: Annotated[
        bool,
        Field(
            description=(
                "If true, the Target authentication is done "
                "through a recorded login sequence."
            )
        ),
    ] = False
    has_sequence_navigation: Optional[bool] = None
    has_basic_auth: Annotated[
        bool,
        Field(
            description=(
                "If true, the Target authentication is done "
                "through username and password credentials."
            )
        ),
    ] = False
    basic_auth: Annotated[
        BasicAuth,
        Field(description="Username and password credentials for the basic auth."),
    ]
    headers: Annotated[List[CookieHeader], Field(description="Custom headers to send.")]
    cookies: Annotated[List[CookieHeader], Field(description="Custom cookies to send.")]
    whitelist: Annotated[
        List, Field(description=("Additional paths to crawl and scan."))
    ] = list()
    blacklist: Annotated[
        List,
        Field(
            description=(
                "URLs to avoid scanning. "
                "The blacklist takes precedence over the whitelist."
            )
        ),
    ] = list()
    changed: Annotated[
        AwareDatetime,
        Field(
            description=(
                "Date and time of the last change, in ISO 8601 UTC format.  For"
                ' example, "2023-08-09T13:27.43.8208302".'
            )
        ),
    ]
    changed_by: Annotated[SimpleUser, Field(description="User who last made changes.")]
    auth_enabled: Annotated[
        bool,
        Field(description=("If true, the Target has authentication.")),
    ] = False
    logout_condition: Annotated[
        LogoutCondition,
        Field(
            description=("Type of combination of the logout conditions."), max_length=3
        ),
    ] = LogoutCondition.any
    check_session_url: Annotated[str, Field(description="URL to check session.")] = ""
    has_otp: Annotated[
        bool,
        Field(description=("If true, the Target has two-factor authentication (2FA).")),
    ] = False
    otp_secret: Annotated[
        str,
        Field(
            description=(
                "The seed/secret obtained when the QR code is displayed to be scanned"
                " by the third-party authenticator (TPA) app installed on the phone"
                " (e.g., Google Authenticator, 1Password, Authy, Microsoft"
                " Authenticator, etc.)."
            )
        ),
    ] = ""
    otp_algorithm: Annotated[
        OtpAlgorithm,
        Field(
            description=(
                "Secure hash algorithm (SHA) to generate the one-time password (OTP)."
            ),
            max_length=12,
        ),
    ] = OtpAlgorithm.SHA1
    otp_digits: Annotated[
        OtpDigits,
        Field(description=("Number of digits of the one-time password (OTP)")),
    ] = 6
    otp_field: Annotated[
        str,
        Field(
            description=(
                "CSS selector of the HTML element in the page to enter the one-time"
                " password (OTP). For example, a text input field."
            )
        ),
    ] = ""
    otp_submit: Annotated[
        str,
        Field(
            description=(
                "CSS selector of the HTML element in the page to submit the one-time"
                " password (OTP). For example, a button."
            )
        ),
    ] = ""
    otp_login_sequence_totp_value: Annotated[
        str,
        Field(
            description=(
                "One-time password (OTP) obtained at the time when the login sequence"
                " was recorded, i.e., the time-based one-time password (TOTP). "
                ' Defaults to "".'
            ),
            max_length=8,
        ),
    ] = ""
    otp_type: Annotated[
        OTPTypes,
        Field(description="Type of one-time password (OTP) technology", max_length=12),
    ] = OTPTypes.TOTP
    otp_url: Union[AnyUrl, Literal[""], None] = None


class Target(TargetBase):
    stack: Annotated[
        List[Framework],
        Field(
            description=(
                "Technologies identified in Target during scans. "
                "The scanning engine uses them to fine-tune vulnerability tests "
                "and improve the explanation of how to fix the vulnerabilities."
            )
        ),
    ]
    verified: Annotated[bool, Field(description="If true, the Domain is verified.")]
    verification_token: Annotated[
        str,
        Field(description="Token used to verify the Domain of the Target."),
    ]
    verification_date: Annotated[
        Optional[AwareDatetime],
        Field(
            description=(
                "Date and time of the verification of the domain, in ISO 8601 UTC format. "
                ' For example, "2023-08-09T13:27.43.8208302".'
            )
        ),
    ] = None
    verification_method: Annotated[
        Union[VerificationMethod, Literal[""]],
        Field(description=("Method used in the Domain verification.")),
    ] = ""
    verification_last_error: Annotated[
        str,
        Field(
            description=("Error of the last verification of the Domain of the Target.")
        ),
    ]
    api_scan_settings: Annotated[
        Optional[APIScanSettings],
        Field(description="Scanning settings if the Target is an API."),
    ] = None


class SimpleScope(BaseModel):
    id: str
    name: Annotated[
        str,
        Field(
            description=("Name of the Target."),
            max_length=255,
        ),
    ]
    site: Annotated[
        Target,
        Field(
            description=(
                "Core settings of the Target.  Includes basic Target information"
                " (like the name, description, and URL) and scanning information (like"
                " the authentication and navigation sequences)."
            )
        ),
    ]
    type: Annotated[
        TargetTypeEnum,
        Field(description=("Type of Target")),
    ] = TargetTypeEnum.web
    desc: Optional[str] = ""
    labels: List[ScopeLabel]
    has_assets: bool
    report_fileformat: Annotated[
        ReportFileformat,
        Field(description=("Report format for the Target.")),
    ] = ReportFileformat.pdf
    scanning_agent: Optional[ScanningAgent] = None
    teams: List[SimpleTeam]
    blackout_period: Annotated[
        Optional[BlackoutPeriod],
        Field(
            description="Time window during which scans are temporarily interrupted."
        ),
    ] = None


class ReviewStatus(str, Enum):
    notrequired = "notrequired"
    pending = "pending"
    rejected = "rejected"
    accepted = "accepted"
    none = ""


class Finding(BaseModel):
    id: int
    target: SimpleScope
    scans: Annotated[
        List[str],
        Field(description="Scans that originated the vulnerability finding."),
    ]
    labels: List[FindingLabel]
    fix: Annotated[
        str, Field(description="Description of how to fix the vulnerability.")
    ]
    requests: Annotated[
        List[RequestResponsePairMarkdown],
        Field(
            description="Pairs of requests and responses of the vulnerability finding."
        ),
    ]
    evidence: Annotated[
        Optional[str],
        Field(description="Evidence with proof of the vulnerability finding."),
    ] = None
    extra: Annotated[
        str, Field(description="Extra details about the vulnerability finding.")
    ]
    definition: SimpleVulnerabilityDefinition
    url: Annotated[
        AnyUrl,
        Field(
            description=("URL of the vulnerability finding."),
        ),
    ]
    path: Annotated[
        AnyUrl,
        Field(description=("URL path of the vulnerability finding")),
    ]
    method: Annotated[
        Union[Method, Literal[""]],
        Field(description=("HTTP method used in the request")),
    ]
    insertion_point: Annotated[
        InsertionPoint,
        Field(description=("Insertion point of the parameter")),
    ]
    parameter: Annotated[
        str,
        Field(
            description=("Name of the inserted parameter."),
            max_length=1024,
        ),
    ]
    value: Annotated[str, Field(description="Value of the inserted parameter.")]
    params: Annotated[
        Optional[Dict[str, List[str]]],
        Field(
            description=(
                "Query parameters of the vulnerability finding, in JSON format."
            )
        ),
    ] = None
    assignee: Optional[SimpleUser] = None
    state: Annotated[
        FindingState,
        Field(description=("State of the vulnerability finding")),
    ]
    severity: Annotated[
        Severity,
        Field(
            description=("Severity of the vulnerability finding: low, medium, or high.")
        ),
    ]
    cvss_score: Annotated[
        float,
        Field(
            description=(
                "Score of the vulnerability finding according to the Common"
                " Vulnerability Scoring System (CVSS)."
            )
        ),
    ]
    cvss_vector: Annotated[
        str,
        Field(
            description=(
                "Vector with the metrics of the score of the vulnerability finding"
                " according to the Common Vulnerability Scoring System (CVSS)."
            )
        ),
    ]
    last_found: Annotated[
        AwareDatetime,
        Field(
            description=(
                "Date and time of when the vulnerability was last found, in ISO 8601"
                ' UTC format.For example, "2023-08-09T13:27:43.8208302"'
            )
        ),
    ]
    retesting: Annotated[
        bool,
        Field(
            description=(
                "If true, the vulnerability will be retested.  If, after the"
                " retest, the vulnerability is no longer found, the vulnerability"
                " finding is marked as fixed. Otherwise, it is marked as not fixed.  "
            )
        ),
    ]
    new: Annotated[
        bool,
        Field(
            description=(
                "If true, this is a newly found vulnerability.If false, this"
                " vulnerability has been found in previous scans."
            )
        ),
    ]
    review_status: Annotated[
        Optional[ReviewStatus],
        Field(
            description=(
                "Some findings we're unsure are valid and need a manual validation"
                " step.\n\n* `notrequired` - not required\n* `pending` - pending"
                " review\n* `rejected` - rejected after review\n* `accepted` - accepted"
                " after review"
            )
        ),
    ] = None
    review_reason: Annotated[
        Optional[str], Field(description="User's reason for finding's review.")
    ] = None
    created_at: Annotated[
        AwareDatetime, Field(description="Timestamp of the Finding's creation.")
    ]
    changed: Annotated[
        AwareDatetime,
        Field(
            description=(
                "Date and time of the last change, in ISO 8601 UTC format.  For"
                ' example, "2023-08-09T13:27.43.8208302".'
            )
        ),
    ]
    changed_by: Annotated[SimpleUser, Field(description="User who last made changes.")]
    comment: Annotated[str, Field(description="Comment on the object.")]


class CodedError(BaseModel):
    code: str
    message: str


class LastLogin(BaseModel):
    status: Annotated[str, Field(description="Status of the login attempt.")]
    timestamp: Annotated[int, Field(description="Timestamp of the login attempt.")]


class CrawledEndpoint(BaseModel):
    jobId: Annotated[
        Optional[int], Field(description="Identifier of the crawler job.")
    ] = None
    status: Annotated[
        Optional[int],
        Field(description="HTTP response status code for the crawler request."),
    ] = None
    method: Annotated[str, Field(description="HTTP method of the crawler request.")]
    url: Annotated[AnyUrl, Field(description="URL of the crawler request.")]


class CrawlerBaseData(BaseModel):
    total: Annotated[int, Field(description="Total number of URLs to crawl.")]
    done: Annotated[int, Field(description="Number of URLs crawled.")]


class CrawlerData(CrawlerBaseData):
    type: Annotated[
        Literal["feedback"],
        Field(description='Type of information. The value is "feedback".'),
    ] = "feedback"
    countTimeoutEndpoints: Annotated[
        int,
        Field(
            description=(
                "Number of requests with timeouts during the crawler execution."
            )
        ),
    ]
    countLoginFailed: Annotated[
        int,
        Field(
            description=(
                "Number of failed login attempts during the crawler execution."
            )
        ),
    ]
    version: Annotated[int, Field(description="Version number.")]
    countNetworkErrorEndpoints: Annotated[
        int,
        Field(description="Number of network errors during the crawler execution."),
    ]
    doingLogin: Annotated[
        bool,
        Field(
            description=(
                "If true, the crawler is currently trying to log in to the Target."
            )
        ),
    ]
    rejected: Annotated[
        int,
        Field(description="Number of URLs deduplicated during the crawler execution."),
    ]
    allExtraHosts: Annotated[List[str], Field(description="List of extra hosts.")]
    crawlingEndpoints: Annotated[
        List[CrawledEndpoint],
        Field(description="List of URLs currently being crawled."),
    ]
    lastLogin: Annotated[List[LastLogin], Field(description="List of the last logins.")]
    status: Annotated[
        Dict[str, Any],
        Field(
            description=(
                "List of HTTP response codes obtained during the crawler execution"
                " and how many of each."
            )
        ),
    ]
    outOfScopeHostsCount: Annotated[
        Dict[str, Any],
        Field(
            description=(
                "List of URLs out of the Target's scope and the number of times the"
                " crawler hit them."
            )
        ),
    ]
    allHostnames: Annotated[
        List[str], Field(description="List of all hostnames to crawl.")
    ]
    lastCrawledEndpoints: Annotated[
        List[CrawledEndpoint],
        Field(description="List of the last crawled URLs."),
    ]
    statusByHost: Annotated[
        Dict[str, Any],
        Field(
            description=(
                "List of HTTP response codes obtained during the crawler execution"
                " and how many of each, grouped by hostname."
            )
        ),
    ]


class CrawlerFullStatus(BaseModel):
    type: Annotated[
        Literal["feedback"],
        Field(description="Type of information. The value is 'feedback'."),
    ]
    iid: Annotated[UUID, Field(description="Internal information.")]
    aid: Annotated[UUID, Field(description="Internal information.")]
    ts: Annotated[float, Field(description="Timestamp of the crawler execution.")]
    subtype: Annotated[
        Literal["status"],
        Field(
            description=('Sub-type of the type of information. The value is "status".')
        ),
    ]
    stage: Annotated[
        Literal["crawler"],
        Field(description="Stage of the scan. The value is 'crawler'."),
    ]
    module: Annotated[
        str, Field(description="Module of the crawler that is executing.")
    ]
    data: Annotated[
        Union[CrawlerData, CrawlerBaseData],
        Field(description="Further details on the crawler execution."),
    ]


class Crawler(BaseModel):
    state: Annotated[str, Field(description=("State of the crawler execution."))]
    status: Annotated[
        List[int],
        Field(
            description=(
                "List with two numbers where the first is the crawled URLs and the"
                " second is the total of URLs to crawl."
            )
        ),
    ]
    warning: Annotated[
        List[CodedError],
        Field(description="List of warnings occurred during the crawler execution."),
    ]
    error: Annotated[
        List[CodedError],
        Field(description="List of errors occurred during the crawler execution."),
    ]
    full_status: Annotated[
        Optional[CrawlerFullStatus],
        Field(description="Detailed information on the crawler execution."),
    ] = None


class FingerprinterSchema(BaseModel):
    state: Annotated[
        str,
        Field(
            description=(
                'State of the fingerprinter execution.  For example, "started" or'
                ' "ended".'
            )
        ),
    ]
    count: Annotated[
        int,
        Field(
            description=(
                "Number of technologies (frameworks) detected by the fingerprinter."
            )
        ),
    ]
    warning: Annotated[
        List[str],
        Field(
            description=(
                "List of warnings occurred during the fingerprinter execution."
            )
        ),
    ]
    error: Annotated[
        List[str],
        Field(
            description=("List of errors occurred during the fingerprinter execution.")
        ),
    ]


class ScannerStateSampleOfRequestBeingScanned(BaseModel):
    httpMethod: Annotated[str, Field(description="HTTP method of the scanner request.")]
    url: Annotated[AnyUrl, Field(description="URL of the scanner request.")]


class ScannerState(BaseModel):
    currentAverageRtt: Annotated[
        float,
        Field(description="Current average response time to scanner requests."),
    ]
    averageRtt: Annotated[
        float,
        Field(description="Overall average response time to scanner requests."),
    ]
    nStatus3xx: Annotated[
        str,
        Field(
            description=(
                "Number of HTTP 3XX response status codes during the scanner execution."
            )
        ),
    ]
    nStatus4xx: Annotated[
        str,
        Field(
            description=(
                "Number of HTTP 4XX response status codes during the scanner execution."
            )
        ),
    ]
    nStatus5xx: Annotated[
        str,
        Field(
            description=(
                "Number of HTTP 5XX response status codes during the scanner execution."
            )
        ),
    ]
    nConnectionErrors: Annotated[
        str,
        Field(description="Number of connection errors during the scanner execution."),
    ]
    nTimeouts: Annotated[
        str,
        Field(description="Number of request timeouts during the scanner execution."),
    ]
    nRequests: Annotated[
        str, Field(description="Number of requests executed by the scanner.")
    ]
    # numberOfRequestBeingScanned: Annotated[
    #     int, Field(description="Number of scanner requests executing.")
    # ]
    # sampleOfRequestBeingScanned: ScannerStateSampleOfRequestBeingScanned
    # NOTE: field above are commented out because they're not present in the API response currently.
    # TODO: check it again when #2756 is resolved


class ScannerData(BaseModel):
    done: Annotated[int, Field(description="Number of URLs scanned.")]
    total: Annotated[int, Field(description="Total number of URLs to scan.")]
    scannerState: Annotated[
        Optional[ScannerState], Field(description="Details on the scanner state.")
    ] = None


class ScannerFullStatus(BaseModel):
    type: Annotated[
        Literal["feedback"],
        Field(description='Type of information.  The value is "feedback".'),
    ]
    iid: Annotated[UUID, Field(description="Internal information.")]
    aid: Annotated[UUID, Field(description="Internal information.")]
    ts: Annotated[float, Field(description="Timestamp of the scanner execution.")]
    subtype: Annotated[
        Literal["status"],
        Field(
            description=('Sub-type of the type of information.  The value is "status".')
        ),
    ]
    stage: Annotated[
        Literal["scanner"],
        Field(description='Stage of the scan.  The value is "scanner".'),
    ]
    module: Annotated[
        str, Field(description="Module of the scanner that is executing.")
    ]
    data: Annotated[
        ScannerData, Field(description="Further details on the scanner execution.")
    ]


class Scanner(BaseModel):
    state: Annotated[
        str,
        Field(
            description=(
                'State of the scanner execution. For example, "started" or "ended".'
            )
        ),
    ]
    status: Annotated[
        List[int],
        Field(
            description=(
                "List with two numbers where the first is the scanned URLs and the"
                " second is the total of URLs to scan."
            )
        ),
    ]
    warning: Annotated[
        List[CodedError],
        Field(description="List of warnings occurred during the scanner execution."),
    ]
    error: Annotated[
        List[Union[str, CodedError]],
        Field(description="List of errors occurred during the scanner execution."),
    ]
    full_status: Annotated[
        Optional[ScannerFullStatus],
        Field(description="Detailed information on the scanner execution."),
    ] = None


class ScanningAgentSchema(BaseModel):
    id: str
    name: Annotated[str, Field(max_length=255)]
    installer_generated: bool
    teams: Optional[List[SimpleTeam]] = None
    online: bool
    fallback: bool
    rx_bytes: int
    tx_bytes: int
    latest_handshake: int


class ScanTargetOptions(BaseModel):
    site: Annotated[
        TargetBase,
        Field(
            description=(
                "The core settings of the Target for the scan. Includes basic"
                " Target information (like the name, description, and URL) and scanning"
                " information (like the authentication and navigation sequences)."
            )
        ),
    ]
    has_assets: Annotated[
        bool,
        Field(description=("If true, the scan includes extra hosts from the Target.")),
    ]
    scanning_agent: Optional[ScanningAgentSchema] = None


class AssessmentStatus(Enum):
    canceled = "canceled"
    canceling = "canceling"
    completed = "completed"
    completed_with_errors = "completed_with_errors"
    failed = "failed"
    paused = "paused"
    pausing = "pausing"
    queued = "queued"
    resuming = "resuming"
    started = "started"
    under_review = "under_review"
    finishing_up = "finishing_up"


class SimpleAssessment(BaseModel):
    id: Annotated[
        str, Field(description="A unique Base58 value identifying this object.")
    ]
    status: AssessmentStatus
    started: Annotated[
        Optional[AwareDatetime],
        Field(description="Date and time of when the scan started."),
    ] = None
    completed: Annotated[
        Optional[AwareDatetime],
        Field(description="Date and time of when the scan was completed."),
    ] = None
    scan_profile: Annotated[str, Field(description="Identifier of the scan profile.")]
    lows: Annotated[
        int, Field(description="Number of vulnerability findings with low severity.")
    ]
    mediums: Annotated[
        int, Field(description="Number of vulnerability findings with medium severity.")
    ]
    highs: Annotated[
        int, Field(description="Number of vulnerability findings with high severity.")
    ]
    criticals: Annotated[
        int,
        Field(description="Number of vulnerability findings with critical severity."),
    ]
    created: AwareDatetime


class RunningAssessment(SimpleAssessment):
    crawler: Annotated[
        Crawler, Field(description="Information on the crawler execution.")
    ]
    fingerprinter: Annotated[
        FingerprinterSchema,
        Field(description="Information on the fingerprinter execution."),
    ]
    scanner: Annotated[
        Scanner, Field(description="Information on the scanner execution.")
    ]
    stack: Annotated[
        List[Framework],
        Field(
            description=(
                "Technologies found in the Scan. The scanning engine uses them to"
                " fine-tune vulnerability tests and texts about how to fix the"
                " vulnerabilities."
            )
        ),
    ]


class Assessment(RunningAssessment):
    target: SimpleScope
    unlimited: Annotated[
        bool,
        Field(
            description=(
                "If true, the scan had unlimited credits. If false, the scan consumed credits"
            )
        ),
    ]
    changed: Annotated[
        AwareDatetime,
        Field(
            description=("Date and time of the last change, in ISO 8601 UTC format.")
        ),
    ]
    changed_by: Annotated[SimpleUser, Field(description="User who last made changes.")]
    target_options: Annotated[
        ScanTargetOptions, Field(description="Options of the Target for the scan.")
    ]
    has_sequence_navigation: Annotated[
        bool,
        Field(description=("If true, the scan includes sequence navigations.")),
    ]
    incremental: Annotated[
        bool,
        Field(
            description=(
                "If true, the scan was incremental to narrow the coverage to new and updated URLs."
            )
        ),
    ]
    reduced_scope: Annotated[
        bool,
        Field(
            description=(
                "If true, the scan used a reduced scope to narrow the coverage to defined URLs. "
            )
        ),
    ]
    crawl_sequences_only: Annotated[
        bool,
        Field(
            description=(
                "If true, the scan only crawled navigation sequences to narrow the coverage."
            )
        ),
    ]
    ignore_blackout_period: Annotated[
        bool,
        Field(
            description=(
                "If true, the scan ignored the blackout period defined in the Target settings."
            )
        ),
    ]
    user_data: Annotated[Optional[str], Field(description="Store scan metadata.")] = (
        None
    )


class SequenceType(str, Enum):
    login = "login"
    navigation = "navigation"


class Sequence(BaseModel):
    id: Annotated[
        str, Field(description="A unique Base58 value identifying this object.")
    ]
    name: str
    requires_authentication: bool
    type: Annotated[
        SequenceType,
        Field(description="* `login` - Login\n* `navigation` - Navigation"),
    ]
    enabled: bool
    index: Optional[int]
    target: Optional[SimpleScope] = None


class SimpleScanProfile(BaseModel):
    id: str
    name: str
    description: str
    builtin: Annotated[
        bool,
        Field(
            description=(
                "If true, it is a built-in Scan profile, "
                "otherwise it is a custom Scan profile."
            )
        ),
    ]


class TargetLessScheduledScan(BaseModel):
    id: Annotated[
        str, Field(description="A unique Base58 value identifying this object.")
    ]
    date_time: Annotated[
        AwareDatetime, Field(description="Date and time of next scan scheduled.")
    ]
    recurrence: Annotated[
        Recurrence,
        Field(description=("Scheduled scan recurrence")),
    ]
    changed: Annotated[
        AwareDatetime,
        Field(
            description=(
                "Date and time of the last change, in ISO 8601 UTC format. For"
                ' example, "2023-08-09T13:27.43.8208302".'
            )
        ),
    ]
    changed_by: Annotated[SimpleUser, Field(description="User who last made changes.")]
    blackout_period: Annotated[
        Optional[BlackoutPeriod],
        Field(
            description="Time window during which scans are temporarily interrupted."
        ),
    ] = None
    timezone: Annotated[
        str,
        Field(
            description="Timezone to use for scheduled scan timestamp.", max_length=64
        ),
    ]
    run_on_day_of_week: Annotated[
        bool,
        Field(
            description=(
                "Schedule Scan to run on specific monthly day of week (for"
                " monthly/quarterly recurrence)."
            )
        ),
    ] = False
    scheduled_day_of_week: Annotated[
        Optional[DayOfWeek],
        Field(description=("Day of week to run scan on - monday to sunday (1-7).")),
    ] = None
    week_index: Annotated[
        Optional[WeekIndex],
        Field(description=("Which week of the month to run scan on")),
    ] = None
    partial_scan: Annotated[
        bool,
        Field(
            description=(
                "Future scans set as partial scans, use in conjunction with"
                " `incremental` and `reduced_scope`."
            )
        ),
    ] = False
    override_target_settings: Annotated[
        bool,
        Field(
            description=(
                "Override Scan Target's Scan settings, use in conjunction with"
                " `override_target_settings`."
            )
        ),
    ] = False
    incremental: Annotated[
        bool,
        Field(
            description=(
                "Future Scans set to incremental, use in conjunction with"
                " `partial_scan` and `override_target_settings`."
            )
        ),
    ] = False
    reduced_scope: Annotated[
        bool,
        Field(
            description=(
                "Future Scans set as reduced scope, use in conjunction with"
                " `partial_scan` and `override_target_settings`."
            )
        ),
    ] = False
    scan_profile: Annotated[Optional[str], Field("Scan profile to use")] = None
    unlimited: Annotated[bool, Field("If true, the Target had unlimited Scans.")] = True


class ScheduledScan(TargetLessScheduledScan):
    target: SimpleScope


class ExtraHost(BaseModel):
    id: Annotated[
        str, Field(description="A unique Base58 value identifying this object.")
    ]
    name: str
    desc: str
    host: Annotated[str, Field(description="Extra host of the target.")]
    stack: Annotated[
        List[Framework],
        Field(
            description=(
                "Technologies identified in Target during scans. "
                "The scanning engine uses them to fine-tune vulnerability tests "
                "and improve the explanation of how to fix the vulnerabilities."
            )
        ),
    ]
    verified: Annotated[bool, Field(description="If true, the Domain is verified.")]
    verification_token: Annotated[
        str,
        Field(description="Token used to verify the Domain of the Target."),
    ]
    verification_date: Annotated[
        Optional[AwareDatetime],
        Field(
            description=(
                "Date and time of the verification of the domain, in ISO 8601 UTC format. "
                ' For example, "2023-08-09T13:27.43.8208302".'
            )
        ),
    ] = None
    verification_method: Annotated[
        Union[VerificationMethod, Literal[""]],
        Field(description=("Method used in the Domain verification.")),
    ] = ""
    verification_last_error: Annotated[
        str,
        Field(
            description=("Error of the last verification of the Domain of the Target.")
        ),
    ]
    changed: Annotated[
        AwareDatetime,
        Field(
            description=(
                "Date and time of the last change, in ISO 8601 UTC format.  For"
                ' example, "2023-08-09T13:27.43.8208302".'
            )
        ),
    ]
    changed_by: Annotated[SimpleUser, Field(description="User who last made changes.")]
    headers: Annotated[List[CookieHeader], Field(description="Custom headers to send.")]
    cookies: Annotated[List[CookieHeader], Field(description="Custom cookies to send.")]
    include: Annotated[
        bool,
        Field(
            description=(
                "If true, the extra host is in the scope of the scan. If false,"
                " the extra host is not in the scope of the scan."
            )
        ),
    ] = True
    target: Optional[SimpleScope] = None


class Scope(BaseModel):
    id: Annotated[
        str, Field(description="A unique Base58 value identifying this object.")
    ]
    site: Annotated[
        Target,
        Field(
            description=(
                "Core settings of the Target. Includes basic Target information"
                " (like the name, description, and URL) and scanning information (like"
                " the authentication and navigation sequences)."
            )
        ),
    ]
    lows: Annotated[
        Optional[int],
        Field(
            description="Number of unresolved vulnerability findings with low severity."
        ),
    ]
    mediums: Annotated[
        Optional[int],
        Field(
            description=(
                "Number of unresolved vulnerability findings with medium severity."
            )
        ),
    ]
    highs: Annotated[
        Optional[int],
        Field(
            description="Number of unresoved vulnerability findings with high severity."
        ),
    ]
    criticals: Annotated[
        Optional[int],
        Field(
            description=(
                "Number of unresolved vulnerability findings with critical severity."
            )
        ),
    ]
    risk: Optional[int]
    last_scan: Annotated[
        Optional[SimpleAssessment], Field(description="Last Scan done for the Target.")
    ] = None
    running_scan: Annotated[
        Optional[RunningAssessment],
        Field(description="Current Scan running for the target."),
    ] = None
    next_scan: Annotated[
        Optional[TargetLessScheduledScan],
        Field(description="Next scheduled scan for the target."),
    ] = None
    assets: List[ExtraHost]
    scan_profile: Annotated[str, Field(description="Identifier of the scan profile.")]
    type: Annotated[
        TargetTypeEnum,
        Field(description=("Type of Target")),
    ] = TargetTypeEnum.web
    unlimited: Annotated[
        bool,
        Field(
            description=(
                "If true, the Target has unlimited scans. If false, the Target"
                " scans consume credits."
            )
        ),
    ] = True
    report_type: Annotated[
        ReportType,
        Field(description=("Type of scan report")),
    ]
    report_fileformat: Annotated[
        ReportFileformat,
        Field(description=("Report format for the Target.")),
    ] = ReportFileformat.pdf
    allowed_scan_profiles: Annotated[
        List[SimpleScanProfile],
        Field(description="Scan profiles allowed for the Target."),
    ]
    labels: List[ScopeLabel]
    scanning_agent: Optional[ScanningAgent] = None
    include_deduplicated_endpoints: Annotated[
        Optional[bool],
        Field(
            description=(
                "If true, scans include deduplicated endpoints. If false or null,"
                " scans exclude deduplicated endpoints.  A deduplicated endpoint has"
                " the same simhash as another scanned endpoint."
            )
        ),
    ] = None
    teams: List[SimpleTeam]
    blackout_period: Annotated[
        Optional[BlackoutPeriod],
        Field(
            description="Time window during which scans are temporarily interrupted."
        ),
    ] = None
    fail_fast: Annotated[
        Optional[bool],
        Field(
            description=(
                "If true, scans fail on recoverable errors. If false, scans"
                " continue on recoverable errors."
            )
        ),
    ] = True
    login_video: Annotated[
        Optional[AnyUrl],
        Field(
            description=(
                "URL for the last recorded login video from this target's scans."
            )
        ),
    ] = None
    changed: Annotated[
        AwareDatetime,
        Field(
            description=("Date and time of the last change, in ISO 8601 UTC format.")
        ),
    ]
    changed_by: Annotated[SimpleUser, Field(description="User who last made changes.")]
    incremental: Annotated[
        bool,
        Field(
            description=(
                "If true, on-demand scans can be incremental to narrow the coverage"
                " to new and updated URLs."
            )
        ),
    ] = False
    reduced_scope: Annotated[
        bool,
        Field(
            description=(
                "If true, on-demand scans can have reduced scope to narrow the"
                " coverage to defined URLs."
            )
        ),
    ] = False
    schedule_incremental: Annotated[
        bool,
        Field(
            description=(
                "If true, scheduled scans can be incremental to narrow the coverage"
            )
        ),
    ] = False
    schedule_reduced_scope: Annotated[
        bool,
        Field(
            description=(
                "If true, scheduled scans can have reduced scope to narrow the"
                " coverage to defined URLs."
            )
        ),
    ] = False
    crawl_sequences_only: Annotated[
        bool,
        Field(
            description=(
                "If true, on-demand scans can only crawl navigation sequences to"
                " narrow the coverage."
            )
        ),
    ] = False
    schedule_crawl_sequences_only: Annotated[
        bool,
        Field(
            description=(
                "If true, scheduled scans can only crawl navigation sequences to"
                " narrow the coverage."
            )
        ),
    ] = False


class Type(Enum):
    web = "web"
    api = "api"


class Speed(Enum):
    integer_10 = 10  # slow
    integer_20 = 20  # medium
    integer_30 = 30  # Fast


class Payloads(Enum):
    integer_10 = 10  # Light
    integer_20 = 20  # Normal
    integer_30 = 30  # Thorough


class Methods(Enum):
    all = "all"
    safe = "safe"
    field_ = ""


class ScanProfile(BaseModel):
    id: Annotated[
        str,
        Field(
            description=(
                "\nIdentifier of the scan profile.  \nCustom scan profiles are always"
                ' prefixed by "sp-".\n'
            )
        ),
    ]
    name: Annotated[
        Optional[str],
        Field(
            description=(
                "\nName of the scan profile.  \nThe maximum length is 255 characters.\n"
            ),
            max_length=255,
        ),
    ] = None
    description: Annotated[
        Optional[str], Field(description="Description of the scan profile.")
    ] = None
    archived: Annotated[
        Optional[bool],
        Field(
            description=(
                "\nIf true, the scan profile is no longer in use.  \nIf false, the scan"
                " profile can be used.\n"
            )
        ),
    ] = None
    type: Annotated[
        Type,
        Field(
            description=(
                "Target type:\n\n* `web` - Scan a Web application, including Single"
                " Page Applications (SPA) that rely on one or more APIs.\n* `api` -"
                " Scan a standalone API defined by an OpenAPI schema, or by a Postman"
                " Collection."
            )
        ),
    ]
    speed: Annotated[
        Optional[Speed],
        Field(
            description=(
                "\nScan speed:  \n(Defaults to `20`)\n\n\n* `10` - Slow - Does roughly"
                " half the number of parallel requests of the Normal speed.\n* `20` -"
                " Normal - Offers a good balance between scan duration and the number"
                " of requests performed at the same time to the target.\n* `30` - Fast"
                " - Does roughly twice the number of parallel requests of the Normal"
                " speed."
            )
        ),
    ] = None
    payloads: Annotated[
        Optional[Payloads],
        Field(
            description=(
                "\nScan payloads:  \n(Defaults to `20`)\n\n\n* `10` - Light - Uses"
                " slightly less payloads than Normal, reducing scan time while still"
                " detecting the most common situations.\n* `20` - Normal - Uses a set"
                " of payloads that maximizes detection without increasing the scan time"
                " excessively, delivering a good compromise.\n* `30` - Thorough -"
                " Includes a more extensive set of payloads to detect very uncommon"
                " situations. Scan time increases significantly."
            )
        ),
    ] = None
    vulnerabilities: Annotated[
        List[SimpleVulnerabilityDefinition],
        Field(description="Vulnerabilities for the scanner to verify."),
    ]
    methods: Annotated[
        Optional[Methods],
        Field(
            description=(
                "\nScan methods:  \n(Defaults to `all`)\n\n\n* `all` - All methods -"
                " Allow any HTTP method to be used during the scan.\n* `safe` - Only"
                " safe methods - Ideal set for production targets, allowing only the"
                " following HTTP methods: GET, HEAD, OPTIONS, TRACE, and CONNECT."
            )
        ),
    ] = None
    can_scan_unverified: Annotated[
        bool,
        Field(
            description=(
                "If true, the scan profile allows targets with unverified domains."
            )
        ),
    ]
    delay: Annotated[
        Optional[int],
        Field(
            description=(
                "\nTime delay in milliseconds between requests for each scanning"
                " thread.  \nIt is an approximate value and is more accurate for slower"
                " scan speed settings.  \nIf not defined, there is no delay between"
                " requests.  \nThe maximum delay is 5000ms.  \n"
            ),
            ge=0,
            le=5000,
        ),
    ] = None
    max_run_time: Annotated[
        Optional[Union[int, str]],
        Field(
            description=(
                '\nThe maximum time the scan is allowed to run.  \nFor example, "750s",'
                ' "25m", "2h", or "1d".  \nSuffix the value with "s" for seconds, "m"'
                ' for minutes, "h" for hours, and "d" for days.  \nIf the units are not'
                " specified the value is considered to be in seconds.  \n"
            )
        ),
    ] = None
    dedup_enabled: Annotated[
        Optional[bool],
        Field(
            description=(
                "\nIf true, the scan deduplicates pages with the same SimHash to scan"
                " only a few of them.  \nIf false, the scan does not deduplicate pages,"
                " which can increase the scan duration significantly.  \nDefaults to"
                " true.  \n"
            )
        ),
    ] = None
    auto_patterns_enabled: Annotated[
        Optional[bool],
        Field(
            description=(
                "\nIf true, the scan detects URL patterns to identify similar pages to"
                " scan only a few of them.  \nIf false, the scan does not detect"
                " patterns, which can increase the scan duration"
                " significantly.\nDefaults to true.  \n"
            )
        ),
    ] = None
    max_urls: Annotated[
        Optional[int],
        Field(
            description=(
                "\nMaximum number of URLs the crawler can visit.  \nThe value must be"
                " between 1 and 50000.  \nDefaults to 5000, which is a good compromise"
                " between coverage and scan time.  \n"
            ),
            ge=1,
            le=50000,
        ),
    ] = None
    builtin: Annotated[
        bool,
        Field(
            description=(
                "\nIf true, it is a [built-in scan"
                " profile](https://help.probely.com/en/articles/1994962-built-in-scan-profiles-and-their-differences),"
                " which cannot be changed.  \nIf false, it is a [custom scan"
                " profile](https://help.probely.com/en/articles/8524283-how-to-customize-a-scan-profile)"
                ' and the id must start with "sp-".\n'
            )
        ),
    ]
