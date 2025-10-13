from abc import (
    ABC,
    abstractmethod
)
from pathlib import Path
from zaparoo_label_automator.wrapper.igdb import IgdbAPI


# abstract base class used to set attributes common to all scrapers
class IgdbScraper(ABC):
    def __init__(
        self,
        output_folder: str,
        upper_batch_limit: int,
        secrets_path: str,
        endpoint_config_file: str,
    ):
        if output_folder is None: 
            raise AttributeError("Error! output_folder must be supplied!")
        if upper_batch_limit is None: 
            raise AttributeError("Error! upper_batch_limit must be supplied!")
        if secrets_path is None: 
            raise AttributeError(f"Error! secrets_path must be supplied!")
        if endpoint_config_file is None: 
            raise AttributeError(f"Error! endpoint_config_file must be supplied!")
        
        # no validations failed 
        self._upper_batch_limit = upper_batch_limit
        self._endpoint_config = endpoint_config_file
        self._output_path = Path(output_folder)
        self._api_client = IgdbAPI(secrets_path=secrets_path)

    @abstractmethod
    def scrape(self):
        pass
