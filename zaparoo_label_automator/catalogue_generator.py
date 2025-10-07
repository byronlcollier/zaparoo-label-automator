"""
Catalogue generator module for selecting games and creating catalogue references.
Handles game selection logic and outputs JSON references for label generation.
"""
import json
from pathlib import Path
from datetime import datetime
from zaparoo_label_automator.platform_logo_selector import PlatformLogoSelector


class CatalogueGenerator:
    """
    Generates game selection catalogues and outputs JSON references for label generation.
    
    This module selects the top-rated games for each platform, ensuring games are only
    assigned to their first release platform to avoid duplicates across platforms.
    """
    
    def __init__(self, catalogue_games_count=20):
        """
        Initialize the catalogue generator.
        
        Args:
            catalogue_games_count (int): Number of games to select per platform
        """
        self.catalogue_games_count = catalogue_games_count
        self.global_game_platform_map = {}  # Track which platform each game was first released on
    
    def generate_catalogues_for_all_platforms(self, reference_data_folder, catalogue_output_folder):
        """
        Generate game selection catalogues for all platforms.
        
        Args:
            reference_data_folder (Path): Path to reference data folder containing platform folders
            catalogue_output_folder (Path): Path to output folder for catalogue JSON
            
        Returns:
            int: Number of platforms processed
        """
        reference_data_folder = Path(reference_data_folder)
        catalogue_output_folder = Path(catalogue_output_folder)
        
        if not reference_data_folder.exists():
            print(f"Reference data folder not found: {reference_data_folder}")
            return 0
        
        # Create catalogue output folder
        catalogue_output_folder.mkdir(parents=True, exist_ok=True)
        
        # First pass: collect all games across all platforms to determine first release platforms
        print("Analyzing games across all platforms to determine first releases...")
        self._build_global_game_platform_map(reference_data_folder)
        
        # Second pass: select games for each platform based on ratings and first release
        print("Selecting games for each platform...")
        catalogue_data = {}
        platforms_processed = 0
        
        for platform_folder in reference_data_folder.iterdir():
            if platform_folder.is_dir():
                try:
                    platform_selection = self._select_games_for_platform(platform_folder)
                    if platform_selection:
                        catalogue_data[platform_folder.name] = platform_selection
                        platforms_processed += 1
                        first_release_count = platform_selection.get('first_release_count', 0)
                        duplicate_count = platform_selection.get('duplicate_count', 0)
                        print(f"Selected {len(platform_selection['games'])} games for {platform_folder.name} "
                              f"({first_release_count} first-release, {duplicate_count} duplicates)")
                except Exception as e:
                    print(f"Error processing platform {platform_folder.name}: {str(e)}")
        
        # Generate final catalogue JSON
        catalogue_json_path = catalogue_output_folder / "game_selection_catalogue.json"
        self._write_catalogue_json(catalogue_data, catalogue_json_path)
        
        print(f"Catalogue selection complete! Generated: {catalogue_json_path}")
        return platforms_processed
    
    def _build_global_game_platform_map(self, reference_data_folder):
        """
        Build a global map of games to their earliest release platform.
        
        Args:
            reference_data_folder (Path): Path to reference data folder
        """
        all_games = {}  # game_id -> {first_release_date, platform_id, platform_name}
        
        for platform_folder in reference_data_folder.iterdir():
            if not platform_folder.is_dir():
                continue
            
            # Read platform info to get platform ID
            platform_info_file = platform_folder / 'platform_info.json'
            if not platform_info_file.exists():
                continue
                
            with open(platform_info_file, 'r', encoding='utf-8') as f:
                platform_info = json.load(f)
            
            platform_id = platform_info.get('id')
            platform_name = platform_info.get('name', platform_folder.name)
            
            # Process each game in this platform
            for game_folder in platform_folder.iterdir():
                if not game_folder.is_dir():
                    continue
                
                game_json_file = game_folder / f"{game_folder.name}.json"
                if not game_json_file.exists():
                    continue
                
                try:
                    with open(game_json_file, 'r', encoding='utf-8') as f:
                        game_data = json.load(f)
                    
                    game_id = game_data.get('id')
                    if not game_id:
                        continue
                    
                    # Find the earliest release date for this game
                    earliest_release_date = self._get_earliest_release_date(game_data)
                    
                    # Check if we've seen this game before
                    if game_id not in all_games:
                        all_games[game_id] = {
                            'first_release_date': earliest_release_date,
                            'platform_id': platform_id,
                            'platform_name': platform_name,
                            'game_name': game_data.get('name', 'Unknown')
                        }
                    else:
                        # Compare release dates to determine which platform was first
                        existing_date = all_games[game_id]['first_release_date']
                        existing_platform_id = all_games[game_id]['platform_id']
                        
                        # Update if this release is earlier, or if same date but lower platform ID (consistent tiebreaker)
                        should_update = False
                        if earliest_release_date and not existing_date:
                            should_update = True
                        elif earliest_release_date and existing_date:
                            if earliest_release_date < existing_date:
                                should_update = True
                            elif earliest_release_date == existing_date and platform_id < existing_platform_id:
                                should_update = True
                        
                        if should_update:
                            all_games[game_id] = {
                                'first_release_date': earliest_release_date,
                                'platform_id': platform_id,
                                'platform_name': platform_name,
                                'game_name': game_data.get('name', 'Unknown')
                            }
                
                except Exception as e:
                    print(f"Warning: Could not process game {game_folder.name}: {str(e)}")
        
        # Store the mapping for use in selection
        self.global_game_platform_map = all_games
        print(f"Analyzed {len(all_games)} unique games across all platforms")
    
    def _get_earliest_release_date(self, game_data):
        """
        Get the earliest release date from game data.
        
        Args:
            game_data (dict): Game data from JSON
            
        Returns:
            str or None: Earliest release date in YYYY-MM-DD format
        """
        # Check first_release_date
        first_release = game_data.get('first_release_date')
        if first_release:
            return first_release
        
        # Check release_dates array
        release_dates = game_data.get('release_dates', [])
        dates = []
        for rd in release_dates:
            date_str = rd.get('date')
            if date_str:
                dates.append(date_str)
        
        if dates:
            return min(dates)  # String comparison works for YYYY-MM-DD format
        
        return None
    
    def _select_games_for_platform(self, platform_folder):
        """
        Select games for a specific platform based on ratings and first release logic.
        
        Args:
            platform_folder (Path): Path to platform folder
            
        Returns:
            dict or None: Platform selection data
        """
        platform_folder = Path(platform_folder)
        
        # Read platform info
        platform_info_file = platform_folder / 'platform_info.json'
        if not platform_info_file.exists():
            return None
        
        with open(platform_info_file, 'r', encoding='utf-8') as f:
            platform_info = json.load(f)
        
        platform_id = platform_info.get('id')
        platform_name = platform_info.get('name', platform_folder.name)
        
        # Collect all games for this platform
        eligible_games = []
        
        for game_folder in platform_folder.iterdir():
            if not game_folder.is_dir():
                continue
            
            game_json_file = game_folder / f"{game_folder.name}.json"
            if not game_json_file.exists():
                continue
            
            try:
                with open(game_json_file, 'r', encoding='utf-8') as f:
                    game_data = json.load(f)
                
                game_id = game_data.get('id')
                if not game_id:
                    continue
                
                # Collect all games, noting if they're first-release on this platform
                game_rating = game_data.get('total_rating', 0) or 0
                is_first_release = self._should_include_game_in_platform(game_id, platform_id)
                
                game_info = {
                    'game_id': game_id,
                    'game_name': game_data.get('name', game_folder.name),
                    'rating': game_rating,
                    'release_date': self._get_earliest_release_date(game_data),
                    'reference_json_path': str(game_json_file.relative_to(platform_folder.parent)),
                    'game_folder_path': str(game_folder.relative_to(platform_folder.parent)),
                    'platform_folder': platform_folder.name,
                    'is_first_release': is_first_release
                }
                
                eligible_games.append(game_info)
            
            except Exception as e:
                print(f"Warning: Could not process game {game_folder.name} for platform {platform_name}: {str(e)}")
        
        # Prioritize first-release games, then fill with others if needed
        selected_games = self._select_games_with_duplicate_minimization(eligible_games)
        
        if not selected_games:
            print(f"Warning: No eligible games found for platform {platform_name}")
            return None
        
        # Count how many are first-release vs duplicates for reporting BEFORE removing the flag
        first_release_count = sum(1 for game in selected_games if game.get('is_first_release', False))
        duplicate_count = len(selected_games) - first_release_count
        
        # Clean up the selected games (remove the internal is_first_release flag)
        for game in selected_games:
            game.pop('is_first_release', None)
        
        return {
            'platform_id': platform_id,
            'platform_name': platform_name,
            'platform_folder': platform_folder.name,
            'total_eligible_games': len(eligible_games),
            'selected_count': len(selected_games),
            'first_release_count': first_release_count,
            'duplicate_count': duplicate_count,
            'games': selected_games,
            'selection_date': datetime.now().isoformat()
        }
    
    def _should_include_game_in_platform(self, game_id, platform_id):
        """
        Determine if a game should be included in a platform's catalogue.
        
        Only includes games where this is the first release platform.
        
        Args:
            game_id: ID of the game
            platform_id: ID of the platform
            
        Returns:
            bool: True if game should be included
        """
        if game_id not in self.global_game_platform_map:
            # Game not in global map, include it (shouldn't happen but handle gracefully)
            return True
        
        # Check if this platform was the first release platform for this game
        first_release_platform = self.global_game_platform_map[game_id]['platform_id']
        return first_release_platform == platform_id
    
    def _select_games_with_duplicate_minimization(self, eligible_games):
        """
        Select games prioritizing first-release games to minimize duplicates,
        but allow duplicates when necessary to fill the quota.
        
        Args:
            eligible_games (list): List of all games available for this platform
            
        Returns:
            list: Selected games for this platform
        """
        # Separate games into first-release and duplicate categories
        first_release_games = [game for game in eligible_games if game.get('is_first_release', False)]
        duplicate_games = [game for game in eligible_games if not game.get('is_first_release', False)]
        
        # Sort both categories by rating (descending)
        first_release_games.sort(key=lambda x: x['rating'], reverse=True)
        duplicate_games.sort(key=lambda x: x['rating'], reverse=True)
        
        selected_games = []
        
        # First, select from first-release games (up to our target count)
        selected_games.extend(first_release_games[:self.catalogue_games_count])
        
        # If we still need more games, fill with highest-rated duplicates
        remaining_slots = self.catalogue_games_count - len(selected_games)
        if remaining_slots > 0:
            selected_games.extend(duplicate_games[:remaining_slots])
        
        return selected_games
    
    def _write_catalogue_json(self, catalogue_data, output_path):
        """
        Write the catalogue selection data to JSON file.
        
        Args:
            catalogue_data (dict): Complete catalogue data
            output_path (Path): Output file path
        """
        # Add metadata to the catalogue
        final_catalogue = {
            'metadata': {
                'generated_date': datetime.now().isoformat(),
                'total_platforms': len(catalogue_data),
                'games_per_platform': self.catalogue_games_count,
                'selection_criteria': 'highest_rating_first_release_platform_only'
            },
            'platforms': catalogue_data
        }
        
        # Calculate some summary statistics
        total_selected_games = sum(len(platform_data['games']) for platform_data in catalogue_data.values())
        total_first_release = sum(platform_data.get('first_release_count', 0) for platform_data in catalogue_data.values())
        total_duplicates = sum(platform_data.get('duplicate_count', 0) for platform_data in catalogue_data.values())
        
        final_catalogue['metadata']['total_selected_games'] = total_selected_games
        final_catalogue['metadata']['total_first_release_games'] = total_first_release
        final_catalogue['metadata']['total_duplicate_games'] = total_duplicates
        final_catalogue['metadata']['duplicate_percentage'] = round((total_duplicates / total_selected_games * 100), 1) if total_selected_games > 0 else 0
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_catalogue, f, indent=2, ensure_ascii=False)
        
        duplicate_percentage = final_catalogue['metadata']['duplicate_percentage']
        print(f"Wrote catalogue selection: {total_selected_games} games across {len(catalogue_data)} platforms")
        print(f"  - {total_first_release} first-release games ({100-duplicate_percentage:.1f}%)")
        print(f"  - {total_duplicates} duplicate games ({duplicate_percentage:.1f}%)")