"""
Catalogue generator module for selecting games and creating catalogue references.
Handles game selection logic and outputs JSON references for label generation.
Also generates PDF catalogues for each platform.
"""
import json
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import weasyprint
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
        
        # Set up Jinja2 template environment
        template_dir = Path(__file__).parent
        self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))
        self.template = self.jinja_env.get_template('catalogue_template.html')
    
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
    
    def generate_pdf_catalogues_from_json(self, catalogue_json_path, reference_data_folder, pdf_output_folder):
        """
        Generate PDF catalogues for each platform using the JSON catalogue.
        
        Args:
            catalogue_json_path (Path): Path to catalogue JSON file
            reference_data_folder (Path): Path to reference data folder
            pdf_output_folder (Path): Path to output folder for PDF catalogues
            
        Returns:
            int: Number of PDFs generated
        """
        catalogue_json_path = Path(catalogue_json_path)
        reference_data_folder = Path(reference_data_folder)
        pdf_output_folder = Path(pdf_output_folder)
        
        if not catalogue_json_path.exists():
            print(f"Catalogue JSON not found: {catalogue_json_path}")
            return 0
        
        # Load catalogue data
        with open(catalogue_json_path, 'r', encoding='utf-8') as f:
            catalogue_data = json.load(f)
        
        # Create PDF output folder
        pdf_output_folder.mkdir(parents=True, exist_ok=True)
        
        pdfs_generated = 0
        
        # Generate PDF for each platform
        for platform_name, platform_selection in catalogue_data['platforms'].items():
            print(f"Generating PDF catalogue for {platform_name}...")
            
            platform_folder = reference_data_folder / platform_selection['platform_folder']
            if not platform_folder.exists():
                print(f"Warning: Platform folder not found: {platform_folder}")
                continue
            
            try:
                success = self._generate_platform_pdf(
                    platform_folder=platform_folder,
                    platform_selection=platform_selection,
                    reference_data_folder=reference_data_folder,
                    pdf_output_folder=pdf_output_folder
                )
                if success:
                    pdfs_generated += 1
            except Exception as e:
                print(f"Error generating PDF for {platform_name}: {str(e)}")
        
        return pdfs_generated
    
    def _generate_platform_pdf(self, platform_folder, platform_selection, reference_data_folder, pdf_output_folder):
        """
        Generate a PDF catalogue for a single platform.
        
        Args:
            platform_folder (Path): Path to platform folder
            platform_selection (dict): Platform selection data from JSON catalogue
            reference_data_folder (Path): Path to reference data folder
            pdf_output_folder (Path): Path to output folder for PDF
            
        Returns:
            bool: True if successful
        """
        # Read platform info
        platform_info_file = platform_folder / 'platform_info.json'
        if not platform_info_file.exists():
            print(f"Warning: No platform_info.json found in {platform_folder}")
            return False
        
        with open(platform_info_file, 'r', encoding='utf-8') as f:
            platform_info = json.load(f)
        
        # Extract platform data
        platform_data = self._extract_platform_data(platform_info, platform_folder)
        
        # Collect games data for selected games only
        games_data = self._collect_selected_games_data(platform_selection, reference_data_folder)
        
        # Generate HTML from template
        html_content = self.template.render(
            platform_name=platform_data['name'],
            platform_logo=platform_data['logo'],
            platform_summary=platform_data['summary'],
            platform_versions=platform_data['versions'],
            games=games_data,
            generation_date=datetime.now().strftime('%B %d, %Y'),
            total_games=len(games_data)
        )
        
        # Generate PDF with WeasyPrint
        pdf_filename = f"{self._sanitize_filename(platform_data['name'])}_Catalogue.pdf"
        pdf_path = pdf_output_folder / pdf_filename
        
        try:
            weasyprint.HTML(string=html_content).write_pdf(str(pdf_path))
            print(f"Generated catalogue: {pdf_path}")
            return True
        except Exception as e:
            print(f"Error generating PDF for {platform_folder.name}: {str(e)}")
            return False
    
    def _extract_platform_data(self, platform_info, platform_folder):
        """Extract and format platform data for PDF generation."""
        # Find platform logo using the platform logo selector
        platform_logo = None
        logo_path = PlatformLogoSelector.find_platform_logo_path(platform_info, platform_folder)
        if logo_path:
            platform_logo = logo_path.absolute().as_uri()
        
        # Extract versions data and sort chronologically
        raw_versions = platform_info.get('versions', [])
        sorted_versions = PlatformLogoSelector.sort_versions_chronologically(raw_versions)
        
        versions = []
        for version in sorted_versions:
            version_data = {
                'name': version.get('name', 'Unknown Version'),
                'summary': self._process_text(version.get('summary', '')),
                'logo': None,
                'releases': []
            }
            
            # Version logo
            if version.get('platform_logo', {}).get('local_file_path'):
                logo_path = platform_folder / version['platform_logo']['local_file_path']
                if logo_path.exists():
                    version_data['logo'] = logo_path.absolute().as_uri()
            
            # Release info - use platform_version_release_dates for versions
            for release in version.get('platform_version_release_dates', []):
                if release.get('date'):
                    date_str = self._format_date_ordinal(release['date'])
                    region = release.get('release_region', {}).get('region', 'Unknown')
                    region_display = region.replace('_', ' ').title()
                    
                    # Add any additional release information
                    additional_info = []
                    if release.get('category'):
                        additional_info.append(release['category'])
                    if release.get('platform_version'):
                        additional_info.append(release['platform_version'])
                    
                    version_data['releases'].append({
                        'date': date_str,
                        'region': region_display,
                        'additional_info': ', '.join(additional_info) if additional_info else None
                    })
            
            # Sort releases by date for this version
            version_data['releases'].sort(key=lambda x: x['date'])
            
            if version_data['releases'] or version_data['summary']:
                versions.append(version_data)
        
        return {
            'name': platform_info.get('name', platform_folder.name),
            'logo': platform_logo,
            'summary': self._process_text(platform_info.get('summary', '')),
            'versions': versions
        }
    
    def _collect_selected_games_data(self, platform_selection, reference_data_folder):
        """
        Collect games data for selected games only.
        
        Args:
            platform_selection (dict): Platform selection data from JSON catalogue
            reference_data_folder (Path): Path to reference data folder
            
        Returns:
            list: List of game data dictionaries
        """
        games = []
        
        for game_info in platform_selection['games']:
            game_folder_path = reference_data_folder / game_info['game_folder_path']
            
            if not game_folder_path.exists():
                continue
            
            game_json_file = game_folder_path / f"{game_folder_path.name}.json"
            if not game_json_file.exists():
                continue
            
            try:
                with open(game_json_file, 'r', encoding='utf-8') as f:
                    game_data = json.load(f)
                
                # Find cover image
                cover_path = None
                for file in game_folder_path.glob("cover_*"):
                    if file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']:
                        cover_path = file.absolute().as_uri()
                        break
                
                # Extract game info
                game_dict = {
                    'name': game_data.get('name', game_folder_path.name),
                    'cover_path': cover_path,
                    'release_date': self._format_date_ordinal(game_data.get('first_release_date')),
                    'genres': [g.get('name', '') for g in game_data.get('genres', [])[:4]],  # Limit to 4
                    'developer': self._get_developer(game_data),
                    'summary': self._process_text(game_data.get('summary', '')),
                    'rating': game_data.get('total_rating')
                }
                
                # Format rating
                if game_dict['rating']:
                    game_dict['rating'] = int(game_dict['rating'])
                
                games.append(game_dict)
                
            except Exception as e:
                print(f"Warning: Could not process game {game_folder_path.name}: {str(e)}")
                continue
        
        return games
    
    def _get_developer(self, game_data):
        """Extract developer name from game data."""
        involved_companies = game_data.get('involved_companies', [])
        for company in involved_companies:
            if company.get('developer', False):
                return company.get('company', {}).get('name', '')
        return None
    
    def _format_date_ordinal(self, timestamp):
        """Format Unix timestamp or date string to ordinal date format (e.g., '1st January 2020')."""
        if not timestamp:
            return None
        
        def get_ordinal_suffix(day):
            """Get the ordinal suffix for a day (st, nd, rd, th)."""
            if 10 <= day % 100 <= 20:
                suffix = 'th'
            else:
                suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
            return suffix
        
        try:
            if isinstance(timestamp, str):
                # Try parsing ISO date
                date_obj = datetime.strptime(timestamp, '%Y-%m-%d')
            else:
                # Unix timestamp
                date_obj = datetime.fromtimestamp(timestamp)
            
            day = date_obj.day
            month = date_obj.strftime('%B')
            year = date_obj.year
            suffix = get_ordinal_suffix(day)
            
            return f"{day}{suffix} {month} {year}"
        except:
            return str(timestamp)
    
    def _process_text(self, text):
        """Process text for HTML output."""
        if not text:
            return ""
        
        # Handle escaped characters
        text = text.replace('\\n', '<br>')
        text = text.replace('\\t', ' ')
        text = text.replace('\\r', '')
        text = text.replace('\\"', '"')
        text = text.replace("\\'", "'")
        text = text.replace('\\\\', '\\')
        
        # Handle actual newlines
        text = text.replace('\n', '<br>')
        text = text.replace('\r', '')
        
        # Clean up spaces
        import re
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def _sanitize_filename(self, filename):
        """Sanitize filename for filesystem safety."""
        import re
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'[^\w\s-]', '', filename).strip()
        filename = re.sub(r'[-\s]+', '_', filename)
        return filename[:50]