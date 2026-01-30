import json
import logging
import platform
from enum import Enum
from typing import Dict, Optional, Union
from urllib.parse import urlencode

import requests
from requests import Request, Session
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from .. import settings, version
from ..exceptions import ProbelyApiUnavailable, ProbelyMissConfig

logger = logging.getLogger(__name__)


class ProbelyUserAgentEnum(Enum):
    CLI = "ProbelyCLI"
    SDK = "ProbelySDK"


class Probely:
    _instance = None

    def __init__(self, api_key=None):
        from .managers import (
            TargetExtraHostManager,
            FindingManager,
            ScanManager,
            TargetSequenceManager,
            TargetLabelManager,
            TargetManager,
        )

        self.finding: FindingManager = FindingManager()
        self.scans: ScanManager = ScanManager()
        self.targets: TargetManager = TargetManager()
        self.target_labels = TargetLabelManager()
        self.target_sequences = TargetSequenceManager()
        self.target_extra_hosts = TargetExtraHostManager()

        self.APP_CONFIG = {
            "api_key": settings.PROBELY_API_KEY,
            "is_cli": settings.IS_CLI,
        }

        if api_key:
            self.APP_CONFIG["api_key"] = api_key

        self._validate_config()

    def __new__(cls, *args, **kwargs):
        raise NotImplementedError("Use Probely.init() to configure")

    def _validate_config(self):
        if self.APP_CONFIG.get("api_key") is None:
            raise ProbelyMissConfig("Missing API_KEY config")

    @classmethod
    def get_config(cls):
        if cls._instance is None:
            cls.init()
        return cls._instance.APP_CONFIG

    @classmethod
    def init(cls, api_key=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        cls._instance.__init__(api_key)
        return cls._instance

    @classmethod
    def reset_config(cls):
        cls._instance = None


class ProbelyAPIClient:
    _session_cache: Union[Session, None] = None

    @classmethod
    def get(
        cls, url, query_params: Optional[Dict] = None, payload: Optional[Dict] = None
    ):
        return cls._send_request("get", url, query_params=query_params, payload=payload)

    @classmethod
    def post(
        cls,
        url,
        query_params: Optional[Dict] = None,
        payload: Optional[Dict] = None,
        files: Optional[Dict] = None,
    ):
        return cls._send_request(
            "post", url, query_params=query_params, payload=payload, files=files
        )

    @classmethod
    def patch(
        cls, url, query_params: Optional[Dict] = None, payload: Optional[Dict] = None
    ):
        return cls._send_request(
            "patch", url, query_params=query_params, payload=payload
        )

    @classmethod
    def delete(
        cls, url, query_params: Optional[Dict] = None, payload: Optional[Dict] = None
    ):
        return cls._send_request(
            "delete", url, query_params=query_params, payload=payload
        )

    @classmethod
    def _send_request(
        cls,
        method: str,
        url: str,
        payload: Optional[Dict] = None,
        query_params: Optional[Dict] = None,
        files: Optional[Dict] = None,
    ):
        if query_params:
            url = f"{url}?{urlencode(query_params, True)}"

        if payload is None:
            payload = {}

        request = Request(method, url=url, json=payload, files=files)

        return cls._call_probely_api(request)

    @classmethod
    def _call_probely_api(cls, request):
        session: Session = cls._build_session()
        prepared_request = session.prepare_request(request)

        logger.debug(
            "Requesting probely API. Method: %s, URL: %s, payload: %s"
            % (prepared_request.method, prepared_request.url, prepared_request.body)
        )
        try:
            resp = session.send(prepared_request)
        except requests.exceptions.RequestException as e:
            logger.debug(f"API request failed. {str(e)}")
            raise ProbelyApiUnavailable

        logger.debug(
            "Probely API response status: %s, content: %s",
            resp.status_code,
            resp.content,
        )

        status_code = resp.status_code
        try:
            content = {} if resp.content == b"" else json.loads(resp.content)
        except json.JSONDecodeError:  # todo: needs testing
            logger.debug(
                "Something wrong with the API. Response content is not valid JSON."
            )
            raise ProbelyApiUnavailable

        return status_code, content

    @classmethod
    def _build_session(cls) -> requests.Session:
        if cls._session_cache:
            return cls._session_cache
        session = requests.Session()
        api_key = Probely.get_config()["api_key"]

        debug_message = (
            "Session setup with api_key ************{}".format(api_key[-4:])
            if api_key
            else "No API Key provided"
        )
        logger.debug(debug_message)

        session.headers.update({"Authorization": "JWT " + api_key})
        session.headers.update({"User-Agent": cls._build_user_agent()})

        retries = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        session.mount("https://", HTTPAdapter(max_retries=retries))

        cls._session_cache = session
        return session

    @classmethod
    def flush_session_cache(cls):
        if cls._session_cache is None:
            return

        cls._session_cache.close()
        cls._session_cache = None

    @classmethod
    def _build_user_agent(cls) -> str:
        user_agent = ProbelyUserAgentEnum.SDK.value

        if Probely.get_config()["is_cli"]:
            user_agent = ProbelyUserAgentEnum.CLI.value

        app_details = f"{user_agent}/{version.__version__}"
        python_details = f"Python/{settings.RUNNING_PYTHON_VERSION}"
        system_details = f"{platform.system()}/{platform.release()}"
        return "{} ({}; {})".format(app_details, python_details, system_details)
