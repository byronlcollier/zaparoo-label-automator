# TODO: Split into two modules - one to scrape platforms, one to scrape games
import csv
import json
import shutil
import re
from pathlib import Path
from datetime import datetime
import pycountry
from zaparoo_label_automator.wrapper.generic import GenericRestAPI
from zaparoo_label_automator.wrapper.twitch import TokenManager
from zaparoo_label_automator.image_downloader import ImageDownloader


class IgdbScraper:
    # TODO: Too many parameters
    def __init__(self, platforms_file, games_count, output_folder, config_path, image_config_path, upper_batch_limit, game_endpoint_config, platform_endpoint_config, media_download_config=None):
        self.platforms_file = platforms_file
        self.games_count = games_count
        self.upper_batch_limit = upper_batch_limit
        # TODO: Move out to main.py
        self.token_manager = TokenManager(config_path=config_path)
        self.api_client = GenericRestAPI()
        self.platforms_data = []
        self.output_path = Path(output_folder)
        self.media_download_config = media_download_config or {}
        self.game_endpoint_config = game_endpoint_config
        self.platform_endpoint_config = platform_endpoint_config
        self.image_downloader = ImageDownloader(config_path=image_config_path, media_config=self.media_download_config)
        
    def run(self):
        """Main orchestration method"""
        # Clear output folder
        # how 'bout we don't for now, 'cos this takes a WHILE now
        # TODO: this should be smarter and should instead skip any outputs that already exist
        # self._clear_output_folder()
        
        # Read platforms from CSV
        platforms = self._read_platforms_csv()
        
        # Process each platform
        for platform_id, platform_name in platforms:
            print(f"Processing platform: {platform_name} (ID: {platform_id})")
            
            # Get platform data
            platform_data = self._fetch_platform_data([platform_id])
            
            if not platform_data:
                print(f"Warning: No data found for platform {platform_name} (ID: {platform_id})")
                continue
                
            platform_info = platform_data[0]
            
            # Post-process the platform data
            processed_platform_info = self._post_process_platform_data(platform_info)
            
            # Get games for this platform
            games_data = self._fetch_games_data(platform_id, self.games_count)
            
            # Post-process the games data
            processed_games_data = self._post_process_games_data(games_data)
            
            # Create output folder and files
            self._create_platform_output(processed_platform_info, processed_games_data)
    
    def _clear_output_folder(self):
        """Clear contents of output folder"""
        if self.output_path.exists():
            shutil.rmtree(self.output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
    
    def _read_platforms_csv(self):
        """Read platforms from CSV file"""
        platforms = []
        with open(self.platforms_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Handle potential whitespace in CSV headers
                name_key = next((k for k in row.keys() if k.strip().lower() == 'name'), 'Name')
                id_key = next((k for k in row.keys() if k.strip().lower() == 'id'), 'id')
                
                platform_id = row[id_key].strip()
                platform_name = row[name_key].strip()
                platforms.append((platform_id, platform_name))
        
        print(f"Found {len(platforms)} platforms to process")
        return platforms
    
    def _fetch_platform_data(self, platform_ids):
        """Fetch platform data from IGDB API"""
        # Load platform endpoint configuration
        with open(self.platform_endpoint_config, 'r') as f:
            config = json.load(f)
        
        # Build query with filter
        ids_str = ','.join(platform_ids)
        query_body = f"{config['properties']['body']} where id = ({ids_str}); limit {self.upper_batch_limit};"
        
        # Ensure token is valid
        self.token_manager.initialise_token()
        
        # Get auth headers
        headers = self.token_manager.get_header()
        headers['Content-Type'] = 'text/plain'
        
        # Make API request
        response = self.api_client.request(
            method=config['properties']['http_method'],
            url=config['properties']['endpoint_url'],
            headers=headers,
            body=query_body
        )
        
        return response
    
    def _fetch_games_data(self, platform_id, limit):
        """Fetch games data for a specific platform"""
        # Load games endpoint configuration
        with open(self.game_endpoint_config, 'r') as f:
            config = json.load(f)
        
        # Handle batching if needed
        if limit > self.upper_batch_limit:
            return self._fetch_games_batched(platform_id, limit, config)
        else:
            return self._fetch_games_single(platform_id, limit, config)
    
    def _fetch_games_single(self, platform_id, limit, config):
        """Fetch games in a single request"""
        # Parse the base body and combine where clauses properly
        base_body = config['properties']['body']
        if 'where' in base_body:
            # Insert the platform filter into existing where clause with AND
            query_body = base_body.replace('where ', f'where platforms = ({platform_id}) & ')
        else:
            # No existing where clause, add one
            query_body = f"{base_body} where platforms = ({platform_id});"
        query_body += f" limit {limit};"
        
        # Ensure token is valid
        self.token_manager.initialise_token()
        
        # Get auth headers
        headers = self.token_manager.get_header()
        headers['Content-Type'] = 'text/plain'
        
        # Make API request
        response = self.api_client.request(
            method=config['properties']['http_method'],
            url=config['properties']['endpoint_url'],
            headers=headers,
            body=query_body
        )
        
        return response
    
    def _fetch_games_batched(self, platform_id, total_limit, config):
        """Fetch games using batched requests"""
        all_games = []
        offset = 0
        
        while offset < total_limit:
            batch_limit = min(self.upper_batch_limit, total_limit - offset)
            
            # Parse the base body and combine where clauses properly
            base_body = config['properties']['body']
            if 'where' in base_body:
                # Insert the platform filter into existing where clause with AND
                query_body = base_body.replace('where ', f'where platforms = ({platform_id}) & ')
            else:
                # No existing where clause, add one
                query_body = f"{base_body} where platforms = ({platform_id});"
            query_body += f" limit {batch_limit}; offset {offset};"
            
            # Ensure token is valid
            self.token_manager.initialise_token()
            
            # Get auth headers
            headers = self.token_manager.get_header()
            headers['Content-Type'] = 'text/plain'
            
            # Make API request
            response = self.api_client.request(
                method=config['properties']['http_method'],
                url=config['properties']['endpoint_url'],
                headers=headers,
                body=query_body
            )
            
            all_games.extend(response)
            offset += batch_limit
            
            # Break if we got fewer results than expected (end of data)
            if len(response) < batch_limit:
                break
        
        return all_games
    
    def _create_platform_output(self, platform_info, games_data):
        """Create output folder and JSON files for a platform"""
        # Use name for folder name, fallback to abbreviation or id
        folder_name = (platform_info.get('name') or 
                      platform_info.get('abbreviation', '') or 
                      str(platform_info.get('id', 'unknown')))
        
        # Ensure folder name is filesystem-safe
        folder_name = self._sanitize_folder_name(folder_name)
        
        # Create platform subfolder in the detail directory
        platform_folder = self.output_path / folder_name
        platform_folder.mkdir(parents=True, exist_ok=True)
        
        # Write platform info JSON
        platform_file = platform_folder / 'platform_info.json'
        with open(platform_file, 'w', encoding='utf-8') as f:
            json.dump(platform_info, f, indent=2, ensure_ascii=False)
        
        # Download ALL platform images (no selection logic in phase 1)
        try:
            platform_downloaded_files = self.image_downloader.download_all_images_recursive(platform_info, platform_folder)
            
            # Add local file paths to platform data and write updated JSON
            if platform_downloaded_files:
                platform_info_with_paths = self.image_downloader.add_local_file_paths(platform_info, platform_downloaded_files)
                # Rewrite the platform info with file paths
                with open(platform_file, 'w', encoding='utf-8') as f:
                    json.dump(platform_info_with_paths, f, indent=2, ensure_ascii=False)
                    
        except Exception as e:
            platform_name = platform_info.get('name', 'unknown platform')
            print(f"Error downloading platform images for {platform_name}: {str(e)}")
            raise
        
        # Write individual JSON files for each game and download images
        games_processed = 0
        for game in games_data:
            game_name = game.get('name', 'unknown_game')
            # Sanitize game name for filename
            game_filename = self._sanitize_folder_name(game_name)
            
            # Create game subfolder
            game_folder = platform_folder / game_filename
            game_folder.mkdir(parents=True, exist_ok=True)
            
            # Download ALL images for this game (no media config filtering in phase 1)
            try:
                downloaded_files = self.image_downloader.download_all_images_recursive(game, game_folder)
                
                # Add local file paths to the game data
                game_with_paths = self.image_downloader.add_local_file_paths(game, downloaded_files)
                
                # Write game JSON file with local file paths
                game_file = game_folder / f'{game_filename}.json'
                with open(game_file, 'w', encoding='utf-8') as f:
                    json.dump(game_with_paths, f, indent=2, ensure_ascii=False)
                
                games_processed += 1
                    
            except Exception as e:
                print(f"Error downloading images for {game_name}: {str(e)}")
                raise
        
        print(f"Created output for {folder_name}: {games_processed} games")
    
    # Platform image downloading logic removed - now downloads ALL images in phase 1
    
    # Platform logo selection logic moved to label generator phase
    
    def _sanitize_folder_name(self, name):
        """Sanitize folder name to be filesystem-safe"""
        # Remove or replace characters not allowed in filenames
        # Keep alphanumeric, spaces, hyphens, underscores, and periods
        sanitized = re.sub(r'[<>:"/\\|?*]', '', name)
        # Replace spaces with underscores
        sanitized = sanitized.replace(' ', '_')
        # Remove multiple consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        # Ensure it's not empty
        return sanitized if sanitized else 'unknown_platform'
    
    def _post_process_games_data(self, games_data):
        """Post-process games data to convert dates and country codes"""
        if not games_data:
            return games_data
        
        processed_games = []
        for game in games_data:
            processed_game = self._process_game_fields(game)
            processed_games.append(processed_game)
        
        return processed_games
    
    def _post_process_platform_data(self, platform_data):
        """Post-process platform data to convert dates and country codes"""
        if not platform_data:
            return platform_data
        
        return self._process_game_fields(platform_data)
    
    def _process_game_fields(self, obj):
        """Recursively process game fields to convert dates and country codes"""
        if isinstance(obj, dict):
            processed_obj = {}
            for key, value in obj.items():
                if self._is_date_field(key) and isinstance(value, (int, float)) and value > 0:
                    # Convert Unix timestamp to ISO 8601 date
                    processed_obj[key] = self._convert_unix_to_date(value)
                elif key == 'country' and isinstance(value, int):
                    # Convert numeric country code to alpha-3
                    processed_obj[key] = self._convert_country_code(value)
                else:
                    # Recursively process nested objects
                    processed_obj[key] = self._process_game_fields(value)
            return processed_obj
        elif isinstance(obj, list):
            return [self._process_game_fields(item) for item in obj]
        else:
            return obj
    
    def _is_date_field(self, field_name):
        """Check if a field name indicates it contains a date"""
        date_indicators = ['date', 'release_date', 'first_release_date']
        return any(indicator in field_name.lower() for indicator in date_indicators)
    
    def _convert_unix_to_date(self, unix_timestamp):
        """Convert Unix timestamp to ISO 8601 date format (YYYY-MM-DD)"""
        try:
            dt = datetime.fromtimestamp(unix_timestamp)
            return dt.strftime('%Y-%m-%d')
        except (ValueError, OverflowError, OSError):
            # Return original value if conversion fails
            return unix_timestamp
    
    def _convert_country_code(self, numeric_code):
        """Convert ISO 3166-1 numeric country code to alpha-3 format using pycountry"""
        try:
            # Convert to string with zero-padding to ensure 3 digits
            numeric_str = f"{numeric_code:03d}"
            country = pycountry.countries.get(numeric=numeric_str)
            if country:
                return country.alpha_3
            else:
                # Return original numeric code if not found
                return numeric_code
        except (ValueError, AttributeError, TypeError):
            # Return original value if conversion fails
            return numeric_code
