import json
import os
import functools
# from typing import Callable, Any, Optional, Dict
from requests import (
    post,
    get
)
from wrapper.twitch import TokenManager


class IGDBWrapper:

    def __init__(
        self,
        config_path: str
    ):
        self._token = TokenManager(config_path=config_path)
        self._token.initialise_token()

    @property
    def token(self) -> str:
        return self._token.value

    
