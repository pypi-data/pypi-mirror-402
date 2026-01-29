import requests
import uuid
import threading
import atexit
from typing import Dict, List, Optional, Any, Union
from html import unescape

__all__ = ["ApiConnector"]

from dry_apy_connector.Loggers import ConsoleLogger, LoggerInterface
from dry_apy_connector.DryApiException import DryApiException
from dry_apy_connector.ValidationErrorHandler import (
    get_validation_messages,
)
import json
import decimal


class ApiConnector:
    """
    HTTP API connector with session management and authentication support.

    Supports both credentials-based and token-based authentication.
    Uses requests.Session for efficient connection pooling during logged-in state.
    Thread-safe for concurrent API calls.
    """

    def __init__(
        self, base_address: str, logger: Optional[LoggerInterface] = None
    ) -> None:
        """
        Initialize the API connector.

        Args:
            base_address: Base URL of the API endpoint (e.g., "https://instancename.navigo3.com/API")
            logger: Optional logger instance. If not provided, ConsoleLogger is used.
        """
        self.__base_address = base_address
        self.__logger = logger or ConsoleLogger()
        self.__sessionId: Optional[str] = None
        self.__token: Optional[str] = None
        self.__session: Optional[requests.Session] = None
        self.__lock = threading.RLock()
        atexit.register(self._cleanup)

    def __create_session(self) -> requests.Session:
        if self.__session is not None:
            self.__session.close()
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json;charset=utf-8"})
        return session

    def login_with_credentials(self, login: str, password: str) -> None:
        """
        Authenticate with username and password.

        Creates a new HTTP session and obtains a session ID from the server.
        The session ID is stored and used for subsequent API calls.

        Args:
            login: Username for authentication
            password: Password for authentication

        Raises:
            Exception: If already logged in or if credentials are invalid
            HTTPError: If the login request fails
        """
        with self.__lock:
            if self.__sessionId is not None:
                raise DryApiException("Already logged in")
            if self.__token is not None:
                raise DryApiException(
                    "There is already temporary token in use, if you want to use credentials logout first"
                )
            if not login or not login.strip():
                raise ValueError("Login must not be blank")
            if not password or not password.strip():
                raise ValueError("Password must not be blank")

            self.__session = self.__create_session()

            self.__logger.debug("Trying to log in...")
            res = self.__do_post("/login", {"login": login, "password": password}, {})

            if res.ok:
                self.__sessionId = res.json()["sessionId"]
                self.__session.headers["X-API-Session"] = self.__sessionId
                self.__logger.debug("Successfully logged in.")
            else:
                self.__session.close()
                self.__session = None
                self.__logger.error(res.text)
                res.raise_for_status()

    def login_with_token(self, token: str) -> None:
        """
        Authenticate with a temporary API token.

        Creates a new HTTP session and uses the provided token for authentication.
        The token is stored and used for subsequent API calls.

        Args:
            token: Temporary API token for authentication

        Raises:
            Exception: If already logged in or if a session is already active
        """
        with self.__lock:
            if self.__token is not None:
                raise DryApiException("Already logged in")
            if not token or not token.strip():
                raise ValueError("Token must not be blank")
            if self.__sessionId is not None:
                raise DryApiException(
                    "There is already session id in use, if you want to use token logout first"
                )

            self.__session = self.__create_session()

            self.__token = token
            self.__session.headers["X-Temporary-Token"] = token

    def logout(self) -> None:
        """
        Log out and close the current session.

        Sends a logout request to the server (if logged in with credentials),
        clears authentication data, and closes the HTTP session.

        Raises:
            HTTPError: If the logout request fails (only for credential-based login)
        """
        with self.__lock:
            self.__token = None

            if self.__sessionId is not None:
                self.__logger.debug("Trying to log out...")
                res = self.__do_post("/logout", {"sessionId": self.__sessionId}, {})
                self.__sessionId = None

                if res.ok:
                    self.__logger.debug("Successfully logged out.")
                else:
                    self.__logger.error(res.text)
                    res.raise_for_status()

        self.close()

    def is_logged_in(self) -> bool:

        return self.__sessionId is not None or self.__token is not None

    def close(self) -> None:
        """
        Close the HTTP session.

        This method is automatically called at program exit via atexit.
        It's safe to call multiple times. Can also be used with context manager.
        """
        with self.__lock:
            if self.__session is not None:
                self.__session.close()
                self.__session = None

    def _cleanup(self, log_errors: bool = False) -> None:
        """
        Cleanup method for automatic logout and session closing.

        This is called automatically at program exit via atexit and from __exit__.
        Attempts to logout gracefully, suppressing any exceptions.

        Args:
            log_errors: If True, log errors to the logger. If False, silently suppress.
        """
        try:
            if self.is_logged_in():
                self.logout()
            else:
                self.close()
        except Exception as e:
            if log_errors:
                self.__logger.error(f"Error during logout: {e}")
            self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cleanup(log_errors=True)
        return False

    def execute(self, method: str, input_data: dict | list) -> dict | list:
        """
        Execute a single API method call.

        Convenience method that wraps the method call and returns the output directly.

        Args:
            method: Qualified name of the API method to execute
            input_data: Input data for the method (dict or list)

        Returns:
            The output data from the API method execution

        Raises:
            DryApiException: If not logged in or if the execution fails
        """
        request = ApiConnector.create_request(
            str(uuid.uuid1()),
            method,
            "EXECUTE",
            input_data,
            [],
            None,
        )
        return self.call([request])[0]["output"]

    def execute_endpoint_batch(
        self,
        method: str,
        requests_input_data: List[Union[dict, list]],
        *,
        execution_alias: Optional[str] = None,
        validation_tolerant: bool = False,
        decode_html: bool = True,
    ) -> List[dict]:
        """
        Execute a batch of API requests with the same method.

        Args:
            method: Qualified name of the API method to execute
            requests_input_data: List of input data for the method (dict or list with same structure for each request) for each request
            execution_alias: Optional name for logging purposes (default: "Api requests")
            validation_tolerant: If True, return responses even if validation fails
            decode_html: If True, decode HTML entities in the response

        Returns:
            List of response dictionaries from the API

        Raises:
            DryApiException: If not logged in or if the execution fails
        """
        requests_list = []
        for input_data in requests_input_data:
            requests_list.append(
                ApiConnector.create_request(
                    str(uuid.uuid1()),
                    method,
                    "EXECUTE",
                    input_data,
                    [],
                    None,
                )
            )
        responses = self.call(
            requests_list,
            execution_alias=execution_alias,
            validation_tolerant=validation_tolerant,
            decode_html=decode_html,
        )
        return [response["output"] for response in responses]

    def validate(self, method: str, input_data: dict) -> dict:
        """
        Validate input data for an API method without executing it.

        Args:
            method: Qualified name of the API method to validate
            input_data: Input data to validate

        Returns:
            Validation response from the API

        Raises:
            DryApiException: If not logged in or if the validation request fails
        """
        request = ApiConnector.create_request(
            str(uuid.uuid1()),
            method,
            "VALIDATE",
            input_data,
            None,
            None,
        )
        return self.call([request])[0]

    def call(
        self,
        requests_list: List[Dict[str, Any]],
        *,
        execution_alias: Optional[str] = None,
        validation_tolerant: bool = False,
        decode_html: bool = True,
    ) -> List[dict]:
        """
        Execute one or more API requests in a batch.

        This is the core method for making API calls. It supports batch execution,
        validation error handling, and HTML decoding.

        Args:
            requests_list: List of request dictionaries (created via create_request)
            execution_alias: Optional name for logging purposes (default: "Api requests")
            validation_tolerant: If True, return responses even if validation fails
            decode_html: If True, decode HTML entities in the response

        Returns:
            List of response dictionaries from the API

        Raises:
            DryApiException: If not logged in, if validation fails (when not tolerant),
                           or if the request fails
        """
        if requests_list is None:
            raise ValueError("Requests list must be set")
        if len(requests_list) == 0:
            return []

        if not ((self.__sessionId is not None) != (self.__token is not None)):
            raise DryApiException("Not logged in")
        execution_name = execution_alias or "Api requests"
        same_endpoints = all(
            request["qualifiedName"] == requests_list[0]["qualifiedName"]
            for request in requests_list
        )

        if same_endpoints:
            self.__logger.debug(
                f"Executing {execution_name} ('{requests_list[0]['qualifiedName']}', {len(requests_list)})"
            )
        else:
            self.__logger.debug(f"Executing {execution_name} ({len(requests_list)})")

        res = self.__do_post("/execute", {"requests": requests_list}, {})

        if res.ok:
            millis = round(res.elapsed.total_seconds() * 1000)
            self.__logger.debug(
                f"Executing {execution_name} successfully done. ({millis}ms)"
            )

            return json.loads(res.text, parse_float=decimal.Decimal)["responses"]
        else:
            if (
                res.headers.get("Content-Type") == "application/json;charset=utf-8"
                and (
                    responses := json.loads(res.text, parse_float=decimal.Decimal).get(
                        "responses"
                    )
                )
                is not None
            ):
                if not validation_tolerant:
                    errors, warns = get_validation_messages(
                        responses, name=execution_alias
                    )

                    if len(warns) > 0:
                        self.__logger.warning(warns)

                    if len(errors) > 0:
                        raise DryApiException(errors)

                return responses

            error_msg = res.text.strip("\n")
            if res.status_code == 500:
                error_msg += " (Maybe invalid login token)"
            self.__logger.error(error_msg)

            res.raise_for_status()
            raise DryApiException(f"Request failed with status {res.status_code}")

    @staticmethod
    def create_request(
        request_uuid: str,
        method: str,
        request_type: str,
        input_data: dict | list,
        upsert_path: Optional[List[Optional[int | str]]],
        from_uuid: Optional[str],
        *,
        decode_html: bool = True,
    ) -> dict:
        """
        Create an API request dictionary.

        This static method constructs a properly formatted request object for the API.

        Args:
            request_uuid: Unique identifier for this request
            method: Qualified name of the API method
            request_type: Type of request (e.g., "EXECUTE", "VALIDATE")
            input_data: Input data for the method (dict or list)
            upsert_path: Optional path for upsert operations
            from_uuid: Optional UUID for input mapping from another request
            decode_html: If True, recursively decode HTML entities in input_data

        Returns:
            Formatted request dictionary ready for API submission

        Raises:
            DryApiException: If request_uuid or method is blank, or if input_data is not set
        """
        if not request_uuid or not request_uuid.strip():
            raise ValueError("Request UUID must not be blank")
        if not method or not method.strip():
            raise ValueError("Method must not be blank")
        if input_data is None:
            raise ValueError("Input data must be set")

        request_data = input_data
        if decode_html:
            request_data = ApiConnector._recursive_unescape(input_data)

        data = {
            "input": request_data,
            "qualifiedName": method,
            "requestType": request_type,
            "requestUuid": request_uuid,
        }

        if from_uuid is not None:
            path = ApiConnector.__build_request_from_path(upsert_path or [])
            data["inputMappings"] = [
                {
                    "fromUuid": from_uuid,
                    "fromPath": {"items": path},
                    "toPath": {"items": []},
                }
            ]

        return data

    @staticmethod
    def _recursive_unescape(data):
        if isinstance(data, str):
            return unescape(data)
        elif isinstance(data, dict):
            return {
                key: ApiConnector._recursive_unescape(value)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [ApiConnector._recursive_unescape(item) for item in data]
        else:
            return data

    @staticmethod
    def __build_request_from_path(
        path: List[Optional[int | str]],
    ) -> List[Dict[str, Optional[int | str]]]:
        res: List[Dict[str, Optional[int | str]]] = []

        if path is not None:
            for item in path:
                if isinstance(item, str):
                    res.append({"index": None, "key": item, "type": "KEY"})
                elif isinstance(item, int):
                    res.append({"index": item, "key": None, "type": "INDEX"})
                else:
                    raise DryApiException(
                        f"Unexpected item {item} of type {type(item)}"
                    )

        return res

    def __do_post(
        self, endpoint: str, data: dict, extra_headers: Dict[str, Any]
    ) -> requests.Response:
        if self.__session is None:
            raise DryApiException("No active session - call login first")
        return self.__session.post(
            self.__base_address + endpoint,
            headers=extra_headers if extra_headers else None,
            json=data,
        )
