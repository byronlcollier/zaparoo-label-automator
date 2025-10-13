import csv
from pathlib import Path
from zaparoo_label_automator.scraper.generic import IgdbScraper

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
        # TODO: validate whether any records were actually found in the CSV
        # TODO: change to logger instead of print
        print(f"Found {len(output_list)} IDs in {self._platforms_file}")
        return output_list

    def scrape(self):

        self._requested_platforms = self._get_platforms_from_file()
        
        for platform_id, platform_name in self._requested_platforms:
            # TODO: change to logger instead of print
            print(f"Processing platform name {platform_name} with ID {platform_id})")