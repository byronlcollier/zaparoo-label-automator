import json
import os
import functools
# from typing import Callable, Any, Optional, Dict
from requests import (
    post,
    get
)

class TokenManager:

    _API_CREDENTIALS_FILE = "api_credentials.json"
    _TOKEN_FILE = "token.json"
    # see https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/#client-credentials-grant-flow
    _CLIENT_CREDENTIALS_GRANT_ENDPOINT = "https://id.twitch.tv/oauth2/token"
    # see https://dev.twitch.tv/docs/authentication/validate-tokens/#how-to-validate-a-token
    _TOKEN_VALIDATION_ENDPOINT = "https://id.twitch.tv/oauth2/validate"
    _TWITCH_API_TIMEOUT_SECONDS = 60


    def __init__(
        self,
        config_path: str = "",
    ):
        if config_path is None or config_path == "":
            raise AttributeError("Error! config_path must be provided.")
        self._config_path = config_path
        self._client_id = None
        self._client_secret = None
        # temporary until this is properly set
        self._token = None

    @property
    def value(self) -> str:
        if self._token is None:
            raise AttributeError(
                "Error! Token must first be set by calling initialise_token."
            )

        return self._token

    def _valid_credentials_file(self) -> bool:

        api_creds_path = os.path.join(self._config_path, self._API_CREDENTIALS_FILE)
        if not os.path.exists(api_creds_path):
            # Create template file
            template = {
                "client_id": "",
                "client_secret": ""
            }
            with open(api_creds_path, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=4)
            raise FileNotFoundError(
                f"{self._API_CREDENTIALS_FILE} was not found at {api_creds_path}. "
                f"An empty template has been created. Please fill in required values."
            )

        # Validate credentials file structure
        with open(api_creds_path, 'r', encoding='utf-8') as f:
            creds = json.load(f)

        required_cred_keys = ["client_id", "client_secret"]
        for key in required_cred_keys:
            if key not in creds or not creds[key]:
                raise ValueError(
                    f"{self._API_CREDENTIALS_FILE} is missing required value for '{key}'. "
                    f"Please add this value to {api_creds_path}"
                )

        # If we've got this far without error then we have a valid file.
        return True

    def _valid_token_file(self) -> bool:

        token_path = os.path.join(self._config_path, self._TOKEN_FILE)
        if os.path.exists(token_path):
            with open(token_path, 'r', encoding='utf-8') as f:
                token_data = json.load(f)

            required_token_keys = ["token"]
            for key in required_token_keys:
                if key not in token_data or not token_data[key]:
                    raise ValueError(
                        f"{self._TOKEN_FILE} is missing required value for '{key}'. "
                        f"If you're seeing this error then there's a bug in _valid_token_file."
                    )
            # If we've got this far without error then we have a valid file.
            return True
        else:
            return False

    def _read_token_from_file(self) -> str:

        token_path = os.path.join(self._config_path, self._TOKEN_FILE)

        try:
            with open(token_path, 'r', encoding='utf-8') as f:
                token_data = json.load(f)

            if "token" in token_data and token_data["token"]:
                return token_data["token"]
            else:
                raise AttributeError(
                    f"The token file {token_path} appears to have invalid structure. "
                    f"If you're seeing this error then there's a bug in _valid_token_file."
                )
        except (json.JSONDecodeError, IOError) as e:
            raise e

    def _write_token_to_file(self, token_string: str):

        token_path = os.path.join(self._config_path, self._TOKEN_FILE)
        token_data = {"token": token_string}
        with open(token_path, 'w', encoding='utf-8') as f:
            json.dump(token_data, f, indent=4)

    def _read_credentials_from_file(self) -> None:

        api_creds_path = os.path.join(self._config_path, self._API_CREDENTIALS_FILE)
        with open(api_creds_path, 'r', encoding='utf-8') as f:
            creds = json.load(f)
            self._client_id = creds["client_id"]
            self._client_secret = creds["client_secret"]

    def _valid_token(self, token_value: str) -> bool:

        request_headers = {
            'Client-ID': self._client_id,
            'Authorization': (f"Bearer {token_value}"),
        }

        response = get(
            url=self._TOKEN_VALIDATION_ENDPOINT,
            headers=request_headers,
            timeout=self._TWITCH_API_TIMEOUT_SECONDS,
        )

        response.raise_for_status()

        # if no http error then assume a valid token
        return True

    def _get_new_token(self) -> str:

        if not self._valid_credentials_file():
            raise FileNotFoundError(
                "The credentials file is invalid. "
                "If you're seeing this message then there is a bug in _valid_credentials_file."
            )

        self._read_credentials_from_file()

        request_body = f"client_id={self._client_id}&client_secret={self._client_secret}&grant_type=client_credentials"

        response = post(
            url=self._CLIENT_CREDENTIALS_GRANT_ENDPOINT,
            data=request_body,
            timeout=self._TWITCH_API_TIMEOUT_SECONDS,
        )

        response.raise_for_status()

        # if no http error then assume request was good

        api_reply = json.loads(response.text)

        return api_reply["access_token"]

    def initialise_token(self) -> None:
        if self._token is not None:
            if self._valid_token(self._token):
                return

        if self._valid_token_file():
            file_token = self._read_token_from_file()
            if self._valid_token(file_token):
                self._token = file_token
        else:
            fresh_token = self._get_new_token()
            self._write_token_to_file(token_string=fresh_token)
            self._token = fresh_token

    @staticmethod
    def token_validation(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            self.initialise_token()
            return func(self, *args, **kwargs)
        return wrapper

    def get_header(self) -> dict:
        if self._client_id is None:
            self._read_credentials_from_file()

        return {
            "Client-ID": self._client_id,
            "Authorization": f"Bearer {self.value}"
        }
