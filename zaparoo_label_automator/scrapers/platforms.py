import csv
from pathlib import Path
from zaparoo_label_automator.scrapers.generic import IgdbScraper

# TODO: USE ONLY FOR DEBUG
from pprint import pprint

# platform info scraper
class PlatformScraper(IgdbScraper):
    def __init__(
            self,
            output_folder: str,
            upper_batch_limit: int,
            secrets_path: str,
            endpoint_config_file: str,
            platforms_file: str,
            api_timeout: int
        ):
        super().__init__(
            output_folder=output_folder,
            upper_batch_limit=upper_batch_limit,
            secrets_path=secrets_path,
            endpoint_config_file=endpoint_config_file,
            api_timeout=api_timeout
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
        query_body = f"{self._endpoint_config['properties']['body']} where id = ({id_filter}); limit {self._upper_batch_limit};"
        response = self._api_client.request(
            method=self._endpoint_config['properties']['http_method'],
            url=self._endpoint_config['properties']['endpoint_url'],
            body=query_body
        )
        return response

    def scrape(self):
        self._requested_platforms = self._get_platforms_from_file()
        total_requests = len(self._requested_platforms)

        results = []

        for i in range(0, total_requests, self._upper_batch_limit):
            batch_ids = self._requested_platforms[i:i + self._upper_batch_limit]
            batch_results = self._scrape_platform_info(platform_ids=batch_ids)
            results.append(batch_results)

        # TODO: Continue from here. Because holy cow it actually works. Turns out I MIGHT actually know what I'm doing. 
        # at this point the original program would post-process dates and country codes
        # but I'm not sure I want to do that. 
        # so it might just be sufficient to save the file now - check the old program.
        # well at this point the old program would get the games for each platform one at a time.
        # but we can be smarter than that. 
        # will probably want to check the len of the results object to make sure it matches 'requested' count
        # instead of a 'results' list, make that an attribute/property of the class
        # that way we have something to iterate over when it comes to getting games for each platform.
        # we WILL want to iterate platforms one at a time in order to get games because there could be $lots
        # why are we talking about ourselves in plural - there's only ONE person working on this...
        # habit from work I guess...
        pprint(results)