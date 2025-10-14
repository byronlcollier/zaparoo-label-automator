import json
from abc import (
    ABC,
    abstractmethod
)
from pathlib import Path
from zaparoo_label_automator.wrappers.igdb import IgdbAPI


# abstract base class used to set attributes common to all scrapers
class IgdbScraper(ABC):
    def __init__(
        self,
        output_folder: str,
        upper_batch_limit: int,
        secrets_path: str,
        endpoint_config_file: str,
        api_timeout: int
    ):
        if not Path(endpoint_config_file).is_file():
            raise FileNotFoundError(f"Error! Endpoint config file '{endpoint_config_file}' does not exist!")
        
        self._upper_batch_limit = upper_batch_limit
        self._output_path = Path(output_folder)
        self._api_client = IgdbAPI(secrets_path=secrets_path, timeout=api_timeout)

        with open(endpoint_config_file, 'r', encoding='utf-8') as f:
            self._endpoint_config = json.load(f)

    @abstractmethod
    def scrape(self):
        pass
