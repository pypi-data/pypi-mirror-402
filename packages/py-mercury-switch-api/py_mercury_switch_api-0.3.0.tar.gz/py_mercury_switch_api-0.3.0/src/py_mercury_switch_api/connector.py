"""Mercury Switch Connector."""

from __future__ import annotations

import logging
from typing import Any

from .exceptions import (
    LoginFailedError,
    MultipleModelsDetectedError,
    NotLoggedInError,
    PageNotLoadedError,
)
from .fetcher import (
    BaseResponse,
    PageFetcher,
    status_code_no_response,
    status_code_not_found,
)
from .models import (
    MODELS,
    AutodetectedMercuryModel,
)
from .models import (
    MercurySwitchModelNotDetectedError as ModelNotDetectedError,
)
from .parsers import MercurySwitchPageParserError, create_page_parser

_LOGGER = logging.getLogger(__name__)


class MercurySwitchConnector:
    """Representation of a Mercury Switch."""

    def __init__(self, host: str, username: str, password: str) -> None:
        """Initialize Connector Object."""
        self.host = host
        self.username = username
        self.password = password

        # initial values
        self.switch_model: type[AutodetectedMercuryModel] = AutodetectedMercuryModel
        self._page_fetcher = PageFetcher(host)
        self._page_parser = create_page_parser()
        self.ports = 0

        _LOGGER.debug(
            "[MercurySwitchConnector] instance created for host=%s",
            self.host,
        )

    def turn_on_offline_mode(self, path_prefix: str) -> None:
        """Turn on offline mode."""
        self._page_fetcher.turn_on_offline_mode(path_prefix)

    def turn_on_online_mode(self) -> None:
        """Turn on online mode."""
        self._page_fetcher.turn_on_online_mode()

    def get_offline_mode(self) -> bool:
        """Get offline mode status."""
        return self._page_fetcher.offline_mode

    def autodetect_model(self) -> type[AutodetectedMercuryModel]:
        """Detect switch model from system info page."""
        _LOGGER.debug(
            "[MercurySwitchConnector.autodetect_model] called for host=%s", self.host
        )

        for template in AutodetectedMercuryModel.AUTODETECT_TEMPLATES:
            response: BaseResponse | Any | None = None
            url: str = template["url"].format(host=self.host)
            method: str = template["method"]

            if self._page_fetcher.offline_mode:
                response = self._page_fetcher.get_page_from_file(url)
            else:
                try:
                    response = self._page_fetcher.request(method, url)
                except Exception as e:
                    _LOGGER.debug("Error fetching autodetect page: %s", e)
                    continue

            if response and self._page_fetcher.has_ok_status(response):
                # Convert Response to BaseResponse if needed
                if hasattr(response, "text"):
                    base_response = BaseResponse()
                    base_response.status_code = response.status_code
                    base_response.content = response.content
                    base_response.text = response.text
                    response = base_response
                else:
                    # Already BaseResponse
                    pass

                passed_checks_by_model: dict[str, dict[str, bool]] = {}
                matched_models: list[AutodetectedMercuryModel] = []

                for mdl_cls in MODELS:
                    mdl: AutodetectedMercuryModel = mdl_cls()
                    mdl_name = mdl.MODEL_NAME
                    passed_checks_by_model[mdl_name] = {}
                    autodetect_funcs = mdl.get_autodetect_funcs()

                    for func_name, expected_results in autodetect_funcs:
                        try:
                            func_result = getattr(self._page_parser, func_name)(
                                response
                            )
                            check_successful = func_result in expected_results
                            passed_checks_by_model[mdl_name][func_name] = (
                                check_successful
                            )

                            if check_successful and mdl not in matched_models:
                                matched_models.append(mdl)
                        except (AttributeError, MercurySwitchPageParserError) as e:
                            _LOGGER.debug(
                                "Error in autodetect function %s: %s", func_name, e
                            )
                            passed_checks_by_model[mdl_name][func_name] = False

                if len(matched_models) == 1:
                    # set local settings
                    self._set_instance_attributes_by_model(type(matched_models[0]))
                    _LOGGER.info(
                        "[MercurySwitchConnector.autodetect_model] found %s switch.",
                        matched_models[0].MODEL_NAME,
                    )
                    return self.switch_model
                if len(matched_models) > 1:
                    raise MultipleModelsDetectedError(str(matched_models))
                _LOGGER.debug(
                    "[MercurySwitchConnector.autodetect_model] "
                    "passed_checks_by_model=%s matched_models=%s",
                    passed_checks_by_model,
                    matched_models,
                )

        raise ModelNotDetectedError("Could not detect switch model")

    def _set_instance_attributes_by_model(
        self, switch_model: type[AutodetectedMercuryModel]
    ) -> None:
        """Set instance attributes based on detected model."""
        self.switch_model = switch_model
        self.ports = switch_model.PORTS

    def get_unique_id(self) -> str:
        """Return unique identifier from switch model and host address."""
        if self.switch_model.MODEL_NAME == "":
            _LOGGER.debug(
                "[MercurySwitchConnector.get_unique_id] switch_model is None, "
                "try MercurySwitchConnector.autodetect_model"
            )
            self.autodetect_model()
            _LOGGER.debug(
                "[MercurySwitchConnector.get_unique_id] now switch_model is %s",
                str(self.switch_model),
            )
        model_lower = self.switch_model.MODEL_NAME.lower()
        return model_lower + "_" + self.host.replace(".", "_")

    def get_login_cookie(self) -> bool:
        """Login and save returned cookie.

        Note: Some Mercury switches allow access without authentication.
        This method will attempt login, but will return True if pages
        are accessible even if login returns 401.
        """
        if not self.switch_model or self.switch_model.MODEL_NAME == "":
            try:
                self.autodetect_model()
            except ModelNotDetectedError:
                # If we can't autodetect, try to login anyway
                pass

        template = AutodetectedMercuryModel.LOGIN_TEMPLATE
        url: str = template["url"].format(host=self.host)
        method: str = template["method"]

        # Prepare form data
        data: dict[str, str] = {}
        params: dict[str, str] = template["params"]
        for key, value in params.items():
            if value == "_username":
                data[key] = self.username
            elif value == "_password":
                data[key] = self.password
            else:
                data[key] = value

        if self._page_fetcher.offline_mode:
            # In offline mode, assume login succeeds
            self._page_fetcher.set_cookie("session", "offline_session")
            return True

        response: Any | None = None
        try:
            response = self._page_fetcher.request(method, url, data)
        except NotLoggedInError:
            # This shouldn't happen on login, but handle it
            pass
        except Exception as e:
            _LOGGER.debug("Error during login request: %s", e)

        # Convert Response to BaseResponse for parsing
        base_response: BaseResponse | None = None
        if response:
            base_response = BaseResponse()
            base_response.status_code = response.status_code
            base_response.content = response.content
            base_response.text = response.text
            base_response.cookies = response.cookies

        # Parse logonInfo from response to determine if login succeeded
        # logonInfo[0] == 0 means success, != 0 means failure
        login_succeeded = False
        err_type: int | None = None
        if base_response:
            err_type = self._page_parser.parse_logon_info(base_response)
            if err_type is not None:
                if err_type == 0:
                    login_succeeded = True
                    _LOGGER.debug(
                        "[MercurySwitchConnector.get_login_cookie] "
                        "logonInfo indicates login succeeded (errType=0)"
                    )
                else:
                    _LOGGER.debug(
                        "[MercurySwitchConnector.get_login_cookie] "
                        "logonInfo indicates login failed (errType=%d)",
                        err_type,
                    )
                    # Map error types to messages
                    error_messages = {
                        1: "Username or password incorrect",
                        2: "User not allowed to login",
                        3: "Maximum login users reached",
                        4: "Maximum login users reached (16 users)",
                        5: "Session timeout",
                    }
                    error_msg = error_messages.get(
                        err_type, f"Unknown error ({err_type})"
                    )
                    _LOGGER.warning(
                        "[MercurySwitchConnector.get_login_cookie] Login failed: %s",
                        error_msg,
                    )

        # Check if login was successful (by logonInfo or status code)
        if login_succeeded or (response and response.status_code == 200):
            # Try to find a session cookie
            if response:
                cookies = response.cookies
                if cookies:
                    for cookie_name, cookie_value in cookies.items():
                        self._page_fetcher.set_cookie(cookie_name, cookie_value)
                        _LOGGER.debug(
                            "[MercurySwitchConnector.get_login_cookie] Found cookie %s",
                            cookie_name,
                        )
                        return True

                # Some switches might set cookie in response headers
                set_cookie_header = response.headers.get("Set-Cookie")
                if set_cookie_header:
                    # Parse Set-Cookie header
                    cookie_parts = set_cookie_header.split(";")[0].split("=", 1)
                    if len(cookie_parts) == 2:
                        self._page_fetcher.set_cookie(cookie_parts[0], cookie_parts[1])
                        return True

            # If no cookie but login succeeded, return True
            if login_succeeded:
                _LOGGER.debug(
                    "[MercurySwitchConnector.get_login_cookie] "
                    "Login succeeded (logonInfo=0) but no cookie found"
                )
                return True

        # Login failed (401 or logonInfo != 0), but check if pages are accessible anyway
        # Some Mercury switches allow access without authentication
        _LOGGER.debug(
            "[MercurySwitchConnector.get_login_cookie] "
            "Login returned status %s (logonInfo errType=%s), "
            "checking if pages are accessible without auth",
            response.status_code if response else "None",
            err_type if err_type is not None else "unknown",
        )

        # Test if we can access a page without authentication
        try:
            test_url = f"http://{self.host}/SystemInfoRpm.htm"
            test_response = self._page_fetcher.request("get", test_url, None)
            if test_response.status_code == 200 and "info_ds" in test_response.text:
                _LOGGER.info(
                    "[MercurySwitchConnector.get_login_cookie] "
                    "Pages are accessible without authentication, continuing"
                )
                return True
        except Exception as e:
            _LOGGER.debug("Error testing page access: %s", e)

        # If login failed and pages aren't accessible, return False
        _LOGGER.warning(
            "[MercurySwitchConnector.get_login_cookie] "
            "Login failed and pages are not accessible"
        )
        return False

    def fetch_page(
        self, method: str, url: str, data: dict[str, Any] | None = None
    ) -> BaseResponse:
        """Fetch url and retry when first response is a redirect to the login page."""
        if self._page_fetcher.offline_mode:
            return self._page_fetcher.get_page_from_file(url)

        for attempt in range(2):
            try:
                response = self._page_fetcher.request(method, url, data)
                # Convert Response to BaseResponse
                base_response = BaseResponse()
                base_response.status_code = response.status_code
                base_response.content = response.content
                base_response.text = response.text
                base_response.cookies = response.cookies
                return base_response
            except NotLoggedInError as error:
                if attempt == 0 and self.get_login_cookie():
                    continue  # Retry the request if login cookie is available
                message = "Not logged in and unable to login."
                raise LoginFailedError(message) from error
            except Exception as e:
                _LOGGER.error("Error fetching page: %s", e)
                base_response = BaseResponse()
                base_response.status_code = status_code_no_response
                return base_response

        base_response = BaseResponse()
        base_response.status_code = status_code_not_found
        return base_response

    def fetch_page_from_templates(
        self, templates: list[dict[str, Any]]
    ) -> BaseResponse:
        """Return response for 1st successful request from templates."""
        for template in templates:
            url: str = template["url"].format(host=self.host)
            method: str = template["method"]
            data: dict[str, str] | None = None
            if "params" in template:
                data = {}
                params: dict[str, str] = template["params"]
                for key, value in params.items():
                    if value == "_username":
                        data[key] = self.username
                    elif value == "_password":
                        data[key] = self.password
                    else:
                        data[key] = value

            response = self.fetch_page(method, url, data)
            if self._page_fetcher.has_ok_status(response):
                return response

        message = f"Failed to load any page of templates: {templates}"
        raise PageNotLoadedError(message)

    def get_switch_infos(self) -> dict[str, Any]:
        """Return dict with all available statistics."""
        if not self.switch_model.MODEL_NAME:
            self.autodetect_model()

        switch_data: dict[str, Any] = {}

        # Fetch System Info
        response = self.fetch_page_from_templates(
            self.switch_model.SYSTEM_INFO_TEMPLATES
        )
        switch_data.update(self._page_parser.parse_system_info(response))

        # Fetch Port Setting (for port status and speed)
        response = self.fetch_page_from_templates(
            self.switch_model.PORT_SETTING_TEMPLATES
        )
        switch_data.update(self._page_parser.parse_port_setting(response, self.ports))

        # Fetch Port Statistics
        response = self.fetch_page_from_templates(
            self.switch_model.PORT_STATISTICS_TEMPLATES
        )
        switch_data.update(
            self._page_parser.parse_port_statistics(response, self.ports)
        )

        # Fetch VLAN Info (if available)
        try:
            response = self.fetch_page_from_templates(
                self.switch_model.VLAN_8021Q_TEMPLATES
            )
            switch_data.update(self._page_parser.parse_vlan_info(response))
        except PageNotLoadedError:
            # VLAN page might not be available, set defaults
            switch_data["vlan_enabled"] = False
            switch_data["vlan_type"] = "None"
            switch_data["vlan_count"] = 0

        return switch_data
