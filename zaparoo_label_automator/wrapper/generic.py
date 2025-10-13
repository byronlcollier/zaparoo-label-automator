from abc import ABC, abstractmethod
from typing import Literal, Union, Optional
import requests


class GenericRestAPI(ABC):

    def __init__(
        self,
        timeout: Union[int, None] = None
    ):
        if timeout is None:
            self._timeout = 60
        else:
            self._timeout = timeout

        # Initialise with empty headers - subclasses should set this where needed
        self._default_headers: dict = {}

    @abstractmethod
    # abstract method to be implemented by child classes
    def _request_validation(self) -> None:
        pass

    def request(
            self,
            method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"],
            url: Optional[str] = None,
            body: Union[str, dict, list, int, float, bool, None] = None
        ) -> dict:
        if url is None:
            raise AttributeError(
                "Error! REST API URL must be supplied."
            )

        if method is None:
            raise AttributeError(
                "Error! HTTP method must be supplied."
            )

        self._request_validation()

        # Build request parameters - only include headers if any are set
        request_params = {"url": url, "timeout": self._timeout}
        if self._default_headers:
            request_params["headers"] = self._default_headers

        # Handle body based on its type
        if body is not None:
            if isinstance(body, str):
                # Raw text/string data
                request_params["data"] = body
            else:
                # JSON-serializable data (dict, list, int, float, bool)
                request_params["json"] = body

        # Use requests.request() with the specified method
        response = requests.request(method, **request_params)

        response.raise_for_status()

        response_data = response.json()

        return response_data
