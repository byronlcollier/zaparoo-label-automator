import json
import requests
from typing import Literal, Union

from wrapper.twitch import TokenManager


class GenericRestAPI:

    def __init__(
        self,
        timeout: int = None
    ):
        if timeout is None:
            self._timeout = 60
        else:
            self._timeout = timeout

    def request(
            self,
            method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"],
            url: str = None,
            headers: dict = None,
            body: Union[str, dict, list, int, float, bool, None] = None
        ) -> dict:
        if headers is None or url is None:
            raise AttributeError(
                "Error! Both headers and REST API URL must be supplied."
            )
        
        if method is None:
            raise AttributeError(
                "Error! HTTP method must be supplied."
            )

        # Build request parameters dynamically
        request_params = {"url": url, "headers": headers, "timeout": self._timeout}
        
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