"""
Catalogue generator module for creating A4 PDF catalogues from platform and game data.
Migrated from ReportLab to WeasyPrint for superior image quality and maintainability.
"""
import json
from pathlib import Path
from datetime import datetime
import weasyprint
from jinja2 import Template
from zaparoo_label_automator.platform_logo_selector import PlatformLogoSelector


class CatalogueGenerator:
    """
    Generates A4 PDF catalogues for video game platforms and their games.
    Migrated from ReportLab to WeasyPrint for superior image quality and maintainability.
    
    This is a drop-in replacement that maintains the same interface as the original
    ReportLab version but provides much better image quality and simpler code.
    """
    
    def __init__(self):
        """Initialize the catalogue generator with WeasyPrint HTML template."""
        # HTML template with embedded CSS - much cleaner than ReportLab's complex objects
        self.html_template = Template("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ platform_name }} Game Catalogue</title>
    <style>
        @page {
            size: A4;
            margin: 2cm;
        }
        
        body {
            font-family: 'Arial', 'DejaVu Sans', sans-serif;
            line-height: 1.6;
            color: #333;
            font-size: 10pt;
        }
        
        /* Platform Header Section */
        .platform-header {
            text-align: center;
            margin-bottom: 40px;
            page-break-after: avoid;
        }
        
        .platform-title {
            font-size: 28pt;
            font-weight: bold;
            color: #1a472a;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .platform-logo {
            max-width: 400px;
            max-height: 240px;
            margin: 20px auto;
            display: block;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        .platform-info {
            max-width: 600px;
            margin: 0 auto 30px auto;
            text-align: justify;
            font-size: 11pt;
            line-height: 1.7;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #1a472a;
        }
        
        .platform-versions {
            margin: 20px 0;
            text-align: left;
        }
        
        .version-block {
            background: white;
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 15px;
        }
        
        .version-title {
            font-size: 14pt;
            font-weight: bold;
            color: #2d5016;
            margin-bottom: 10px;
        }
        
        .version-info {
            display: flex;
            align-items: flex-start;
            gap: 15px;
        }
        
        .version-logo {
            flex-shrink: 0;
        }
        
        .version-logo img {
            max-width: 120px;
            max-height: 80px;
            border-radius: 4px;
        }
        
        .version-details {
            flex-grow: 1;
            font-size: 10pt;
            line-height: 1.5;
            text-align: left;
        }
        
        .version-details ul {
            margin: 0;
            padding-left: 15px;
        }
        
        .release-info {
            font-weight: bold;
            color: #333;
            margin-bottom: 8px;
        }
        
        /* Games Section */
        .games-section {
            page-break-before: always;
        }
        
        .section-header {
            font-size: 24pt;
            font-weight: bold;
            color: #8b0000;
            border-bottom: 3px solid #8b0000;
            margin: 40px 0 30px 0;
            padding-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        /* Game Grid Layout - Full width */
        .games-grid {
            display: block;
            margin-bottom: 30px;
        }
        
        .game {
            display: flex;
            gap: 20px;
            padding: 20px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            background: white;
            page-break-inside: avoid;
            min-height: 140px;
            margin-bottom: 15px;
            width: 100%;
        }
        
        .game:nth-child(odd) {
            background: #fafafa;
        }
        
        .game-cover {
            flex-shrink: 0;
        }
        
        .game-cover img {
            width: 120px;
            height: 170px;
            object-fit: cover;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.15);
            border: 1px solid #ddd;
        }
        
        .game-info {
            flex-grow: 1;
            min-width: 0; /* Allows text to wrap */
        }
        
        .game-title {
            font-size: 11pt;
            font-weight: bold;
            color: #2d5016;
            margin-bottom: 6px;
            line-height: 1.3;
            word-wrap: break-word;
        }
        
        .game-meta {
            font-size: 8pt;
            color: #666;
            margin-bottom: 6px;
            line-height: 1.4;
        }
        
        .game-meta strong {
            color: #333;
        }
        
        .game-summary {
            font-size: 8pt;
            line-height: 1.4;
            text-align: justify;
            color: #555;
            overflow-wrap: break-word;
        }
        
        /* Ensure consistent high-quality image rendering */
        @media print {
            img {
                image-rendering: -webkit-optimize-contrast;
                image-rendering: crisp-edges;
                image-rendering: pixelated;
            }
        }
        
        /* Page break handling */
        .page-break {
            page-break-before: always;
        }
        
        /* Footer */
        .catalogue-footer {
            margin-top: 40px;
            text-align: center;
            font-size: 8pt;
            color: #888;
            border-top: 1px solid #ddd;
            padding-top: 15px;
        }
    </style>
</head>
<body>
    <!-- Platform Header -->
    <div class="platform-header">
        <h1 class="platform-title">{{ platform_name }}</h1>
        {% if platform_logo %}
        <img src="{{ platform_logo }}" alt="{{ platform_name }} Logo" class="platform-logo">
        {% endif %}
        
        {% if platform_summary %}
        <div class="platform-info">{{ platform_summary | safe }}</div>
        {% endif %}
        
        {% if platform_versions %}
        <div class="platform-versions">
            {% for version in platform_versions %}
            <div class="version-block">
                <div class="version-title">{{ version.name }}</div>
                <div class="version-info">
                    {% if version.logo %}
                    <div class="version-logo">
                        <img src="{{ version.logo }}" alt="{{ version.name }} Logo">
                    </div>
                    {% endif %}
                    <div class="version-details">
                        {% if version.releases %}
                        <div class="release-info">Release Information:</div>
                        <ul>
                        {% for release in version.releases %}
                            <li>{{ release.date }} - {{ release.region }}{% if release.additional_info %} - {{ release.additional_info }}{% endif %}</li>
                        {% endfor %}
                        </ul>
                        {% endif %}
                        {% if version.summary %}
                        <p>{{ version.summary | safe }}</p>
                        {% endif %}
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        {% endif %}
    </div>
    
    <!-- Games Section -->
    {% if games %}
    <div class="games-section">
        <h2 class="section-header">Games Library ({{ games|length }} games)</h2>
        
        <div class="games-grid">
            {% for game in games %}
            <div class="game">
                <div class="game-cover">
                    {% if game.cover_path %}
                    <img src="{{ game.cover_path }}" alt="{{ game.name }} Cover">
                    {% else %}
                    <div style="width: 120px; height: 170px; background: #f0f0f0; border: 1px dashed #ccc; display: flex; align-items: center; justify-content: center; font-size: 10pt; color: #999; text-align: center; border-radius: 4px;">No Cover</div>
                    {% endif %}
                </div>
                <div class="game-info">
                    <div class="game-title">{{ game.name }}</div>
                    <div class="game-meta">
                        {% if game.release_date %}<strong>Released:</strong> {{ game.release_date }}<br>{% endif %}
                        {% if game.genres %}<strong>Genres:</strong> {{ game.genres|join(', ') }}<br>{% endif %}
                        {% if game.developer %}<strong>Developer:</strong> {{ game.developer }}<br>{% endif %}
                        {% if game.rating %}<strong>Rating:</strong> {{ game.rating }}/100{% endif %}
                    </div>
                    {% if game.summary %}
                    <div class="game-summary">{{ game.summary | safe }}</div>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
    {% endif %}
    
    <div class="catalogue-footer">
        Generated on {{ generation_date }} • {{ total_games }} games catalogued
    </div>
</body>
</html>
        """)

    def generate_catalogue_for_platform(self, platform_folder, output_folder):
        """
        Generate a PDF catalogue for a single platform.
        
        This is a drop-in replacement for the ReportLab version that maintains
        the same interface but provides much better image quality.
        
        Args:
            platform_folder (Path): Path to platform folder containing games
            output_folder (Path): Path to output folder for the catalogue
        """
        platform_folder = Path(platform_folder)
        output_folder = Path(output_folder)
        
        if not platform_folder.exists():
            raise FileNotFoundError(f"Platform folder not found: {platform_folder}")
        
        # Read platform info (same as ReportLab version)
        platform_info_file = platform_folder / 'platform_info.json'
        if not platform_info_file.exists():
            print(f"Warning: No platform_info.json found in {platform_folder}")
            return False
        
        with open(platform_info_file, 'r', encoding='utf-8') as f:
            platform_info = json.load(f)
        
        # Create output folder
        output_folder.mkdir(parents=True, exist_ok=True)
        
        # Extract platform data
        platform_data = self._extract_platform_data(platform_info, platform_folder)
        
        # Collect games data
        games_data = self._collect_games_data(platform_folder)
        
        # Generate HTML
        html_content = self.html_template.render(
            platform_name=platform_data['name'],
            platform_logo=platform_data['logo'],
            platform_summary=platform_data['summary'],
            platform_versions=platform_data['versions'],
            games=games_data,
            generation_date=datetime.now().strftime('%B %d, %Y'),
            total_games=len(games_data)
        )
        
        # Generate PDF with WeasyPrint - HIGH QUALITY IMAGES!
        pdf_filename = f"{self._sanitize_filename(platform_data['name'])}_Catalogue.pdf"
        pdf_path = output_folder / pdf_filename
        
        try:
            # WeasyPrint magic - no complex image processing needed!
            weasyprint.HTML(string=html_content).write_pdf(str(pdf_path))
            
            print(f"Generated catalogue: {pdf_path}")
            return True
            
        except Exception as e:
            print(f"Error generating PDF for {platform_folder.name}: {str(e)}")
            return False

    def generate_catalogues_for_all_platforms(self, detail_folder, output_folder):
        """
        Generate catalogues for all platforms in the detail folder.
        
        This maintains the same interface as the ReportLab version.
        
        Args:
            detail_folder (Path): Path to detail folder containing platform folders
            output_folder (Path): Path to output folder for catalogues
        """
        detail_folder = Path(detail_folder)
        output_folder = Path(output_folder)
        
        if not detail_folder.exists():
            print(f"Detail folder not found: {detail_folder}")
            return 0
        
        catalogues_generated = 0
        
        for platform_folder in detail_folder.iterdir():
            if platform_folder.is_dir():
                try:
                    success = self.generate_catalogue_for_platform(platform_folder, output_folder)
                    if success:
                        catalogues_generated += 1
                except Exception as e:
                    print(f"Error generating catalogue for {platform_folder.name}: {str(e)}")
        
        return catalogues_generated

    def _extract_platform_data(self, platform_info, platform_folder):
        """Extract and format platform data."""
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
    
    def _collect_games_data(self, platform_folder):
        """Collect all games data from the platform folder."""
        games = []
        
        for game_folder in sorted(platform_folder.iterdir()):
            if not game_folder.is_dir():
                continue
            
            game_json_file = game_folder / f"{game_folder.name}.json"
            if not game_json_file.exists():
                continue
            
            try:
                with open(game_json_file, 'r', encoding='utf-8') as f:
                    game_data = json.load(f)
                
                # Find cover image
                cover_path = None
                for file in game_folder.glob("cover_*"):
                    if file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']:
                        cover_path = file.absolute().as_uri()
                        break
                
                # Extract game info
                game_info = {
                    'name': game_data.get('name', game_folder.name),
                    'cover_path': cover_path,
                    'release_date': self._format_date_ordinal(game_data.get('first_release_date')),
                    'genres': [g.get('name', '') for g in game_data.get('genres', [])[:4]],  # Limit to 4
                    'developer': self._get_developer(game_data),
                    'summary': self._process_text(game_data.get('summary', '')),
                    'rating': game_data.get('total_rating')
                }
                
                # Format rating
                if game_info['rating']:
                    game_info['rating'] = int(game_info['rating'])
                
                games.append(game_info)
                
            except Exception as e:
                print(f"Warning: Could not process game {game_folder.name}: {str(e)}")
                continue
        
        # Sort games by rating in descending order (highest rated first)
        games.sort(key=lambda x: x['rating'] if x['rating'] is not None else 0, reverse=True)
        
        return games
    
    def _get_developer(self, game_data):
        """Extract developer name from game data."""
        involved_companies = game_data.get('involved_companies', [])
        for company in involved_companies:
            if company.get('developer', False):
                return company.get('company', {}).get('name', '')
        return None
    
    def _format_date(self, timestamp):
        """Format Unix timestamp to readable date."""
        if not timestamp:
            return None
        try:
            if isinstance(timestamp, str):
                # Try parsing ISO date
                date_obj = datetime.strptime(timestamp, '%Y-%m-%d')
                return date_obj.strftime('%B %Y')
            else:
                # Unix timestamp
                return datetime.fromtimestamp(timestamp).strftime('%B %Y')
        except:
            return str(timestamp)
    
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