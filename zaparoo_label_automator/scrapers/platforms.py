import csv
from pathlib import Path
from zaparoo_label_automator.scrapers.generic import IgdbScraper

# platform info scraper
class PlatformScraper(IgdbScraper):
    def __init__(
            self,
            output_folder: str,
            upper_batch_limit: int,
            secrets_path: str,
            endpoint_config_file: str,
            platforms_file: str
        ):
        super().__init__(
            output_folder=output_folder,
            upper_batch_limit=upper_batch_limit,
            secrets_path=secrets_path,
            endpoint_config_file=endpoint_config_file
        )

        if not Path(platforms_file).is_file():
            raise FileExistsError(f"Error! File '{platforms_file}' does not exist!")
        
        self._platforms_file = platforms_file
        self._requested_platforms = []
        
    def _get_platforms_from_file(self) -> list:
        output_list = []
        with open(self._platforms_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Handle potential whitespace in CSV headers
                id_key = next((k for k in row.keys() if k.strip().lower() == 'id'), 'id')                
                platform_id = row[id_key].strip()
                output_list.append(platform_id)
        
        if len(output_list) == 0:
            raise AttributeError(f"Error! {len(output_list)} records found in file '{self._platforms_file}'!")
        # TODO: change to logger instead of print
        print(f"Found {len(output_list)} IDs in {self._platforms_file}")
        return output_list

    def _scrape_platform_info(self, platform_ids: list[int]):
        id_filter = ','.join(platform_ids)
        query_body = f"{self._endpoint_config['properties']['body']} where id = ({id_filter}); limit {self._upper_batch_limit}"

        

    def scrape(self):
        self._requested_platforms = self._get_platforms_from_file()
        total_requests = len(self._requested_platforms)

        for i in range(0, total_requests, self._upper_batch_limit):
            print("do something!")