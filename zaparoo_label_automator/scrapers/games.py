# from csv import DictReader
# from pathlib import Path
from typing import Union
from zaparoo_label_automator.scrapers.generic import IgdbScraper

class GameScraper(IgdbScraper):
    def __init__(
            self,
            output_folder: str,
            upper_batch_limit: int,
            secrets_path: str,
            endpoint_config_file: str,
            api_timeout: int,
            # TODO: Implement later
            games_file: Union[str, None]
        ):

        super().__init__(
            output_folder,
            upper_batch_limit,
            secrets_path,
            endpoint_config_file,
            api_timeout
        )

        # TODO: Implement later
        # self._games_file = games_file

        # if games_file:
        #     if not Path(games_file).is_file():
        #         raise FileExistsError(f"Error! File '{games_file}' does not exist!")
        #     else:
        #         self._games_file = games_file

    # def _get_games_from_file(self) -> list:
    #     output_list = []
    #     with open(self._games_file, 'r', encoding='utf-8') as f: # type: ignore
    #         reader = DictReader(f)
    #         for row in reader:
    #             # Handle potential whitespace in CSV headers
    #             id_key = next((k for k in row.keys() if k.strip().lower() == 'id'), 'id')
    #             platform_id = row[id_key].strip()
    #             output_list.append(platform_id)

    #     if len(output_list) == 0:
    #         raise AttributeError(f"Error! {len(output_list)} records found in file '{self._games_file}'!")
    #     # TODO: change to logger instead of print
    #     print(f"Found {len(output_list)} IDs in {self._games_file}")
    #     return output_list

    def _scrape_game_data(self, platform_id: int) -> list:
        

    def scrape(self, platform_info) -> list:
        game_info = []
        for platform in platform_info:
            print(platform)
