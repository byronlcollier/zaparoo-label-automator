from zaparoo_label_automator.wrappers.twitch import TokenManager
from zaparoo_label_automator.wrappers.generic import GenericRestAPI

# inherits the underlying generic class, but sets the header on init
class IgdbAPI(GenericRestAPI):
    def __init__(
        self,
        timeout: int,
        secrets_path: str,
    ):
        super().__init__(timeout=timeout)
        self._token = TokenManager(config_path=secrets_path)

    def _request_validation(self):
        # init token and set header prior to sending requests
        self._token.initialise_token()
        self._default_headers = self._token.get_header()