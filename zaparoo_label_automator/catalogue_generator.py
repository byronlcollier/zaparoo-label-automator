"""
Catalogue generator module for creating A4 PDF catalogues from platform and game data.
"""
import json
from pathlib import Path
from datetime import datetime
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io


class CatalogueGenerator:
    """
    Generates A4 PDF catalogues for video game platforms and their games.
    """
    
    def __init__(self):
        """Initialize the catalogue generator with A4 page settings."""
        self.page_width, self.page_height = A4
        self.margin = 0.75 * inch
        self.content_width = self.page_width - (2 * self.margin)
        self.content_height = self.page_height - (2 * self.margin)
        
        # Register Unicode-capable fonts
        self._register_unicode_fonts()
        
        # Set up styles
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def _register_unicode_fonts(self):
        """Register Unicode-capable fonts for international character support."""
        try:
            import os
            import platform
            
            # Font paths with better Unicode support
            font_paths = []
            
            if platform.system() == "Darwin":  # macOS
                font_paths.extend([
                    # Try fonts with comprehensive Unicode support first
                    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",  # Best Unicode coverage
                    "/System/Library/Fonts/Supplemental/Arial.ttf",          # Good fallback
                    "/Library/Fonts/Arial Unicode MS.ttf",                   # Alternative location
                    "/System/Library/Fonts/Geneva.ttf",                      # System font with decent Unicode
                    "/System/Library/Fonts/Helvetica.ttc",                   # Basic fallback (TTC)
                ])
            elif platform.system() == "Linux":
                font_paths.extend([
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",  # Google Noto CJK
                ])
            elif platform.system() == "Windows":
                font_paths.extend([
                    "C:/Windows/Fonts/msgothic.ttc",       # MS Gothic - good for Japanese
                    "C:/Windows/Fonts/malgun.ttf",         # Malgun Gothic - good for Korean  
                    "C:/Windows/Fonts/arial.ttf",
                    "C:/Windows/Fonts/calibri.ttf",
                ])
            
            # Try to register the first available font with good Unicode support
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('UnicodeFont', font_path))
                        pdfmetrics.registerFont(TTFont('UnicodeFontBold', font_path))  # Same font, styled bold
                        print(f"Registered Unicode font: {font_path}")
                        
                        # Test if the font actually supports CJK characters
                        test_chars = "ファミリー현대"  # Japanese and Korean test characters
                        print(f"Font should support CJK characters: {test_chars}")
                        return
                    except Exception as e:
                        print(f"Failed to register font {font_path}: {e}")
                        continue
            
            print("No suitable Unicode fonts found, using ReportLab defaults")
            print("Note: Some Unicode characters may not display correctly")
            
        except Exception as e:
            print(f"Error setting up Unicode fonts: {e}")
            print("Using ReportLab default fonts")
    
    def _create_custom_styles(self):
        """Create custom paragraph styles for the catalogue."""
        # Check if Unicode font is available
        unicode_font = 'UnicodeFont' if 'UnicodeFont' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
        unicode_font_bold = 'UnicodeFontBold' if 'UnicodeFontBold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'
        
        # Platform title style
        self.styles.add(ParagraphStyle(
            name='PlatformTitle',
            parent=self.styles['Heading1'],
            fontName=unicode_font_bold,
            fontSize=24,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Platform info style
        self.styles.add(ParagraphStyle(
            name='PlatformInfo',
            parent=self.styles['Normal'],
            fontName=unicode_font,
            fontSize=12,
            spaceAfter=12,
            alignment=TA_JUSTIFY
        ))
        
        # Game title style
        self.styles.add(ParagraphStyle(
            name='GameTitle',
            parent=self.styles['Heading2'],
            fontName=unicode_font_bold,
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.darkgreen
        ))
        
        # Game info style
        self.styles.add(ParagraphStyle(
            name='GameInfo',
            parent=self.styles['Normal'],
            fontName=unicode_font,
            fontSize=10,
            spaceAfter=8
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontName=unicode_font_bold,
            fontSize=18,
            spaceBefore=30,
            spaceAfter=15,
            textColor=colors.darkred
        ))
        
        # Update the default Normal style to use Unicode font
        self.styles['Normal'].fontName = unicode_font
    
    def generate_catalogue_for_platform(self, platform_folder, output_folder):
        """
        Generate a PDF catalogue for a single platform.
        
        Args:
            platform_folder (Path): Path to platform folder containing games
            output_folder (Path): Path to output folder for the catalogue
        """
        platform_folder = Path(platform_folder)
        output_folder = Path(output_folder)
        
        if not platform_folder.exists():
            raise FileNotFoundError(f"Platform folder not found: {platform_folder}")
        
        # Read platform info
        platform_info_file = platform_folder / 'platform_info.json'
        if not platform_info_file.exists():
            print(f"Warning: No platform_info.json found in {platform_folder}")
            return False
        
        with open(platform_info_file, 'r', encoding='utf-8') as f:
            platform_info = json.load(f)
        
        # Create output folder if it doesn't exist
        output_folder.mkdir(parents=True, exist_ok=True)
        
        # Generate PDF filename
        platform_name = platform_info.get('name', 'Unknown Platform')
        safe_name = self._sanitize_filename(platform_name)
        pdf_filename = f"{safe_name}_Catalogue.pdf"
        pdf_path = output_folder / pdf_filename
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=A4,
            leftMargin=self.margin,
            rightMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        # Build content
        story = []
        
        # Add platform information
        self._add_platform_section(story, platform_info, platform_folder)
        
        # Add games section
        self._add_games_section(story, platform_folder)
        
        # Build PDF
        try:
            doc.build(story)
            print(f"Generated catalogue: {pdf_filename}")
            return True
        except Exception as e:
            print(f"Error generating catalogue for {platform_name}: {str(e)}")
            return False
    
    def _add_platform_section(self, story, platform_info, platform_folder):
        """Add platform information section to the story."""
        # Platform title
        platform_name = platform_info.get('name', 'Unknown Platform')
        story.append(Paragraph(platform_name, self.styles['PlatformTitle']))
        
        # Platform logo (if available)
        logo_path, logo_json = self._find_platform_logo_with_json(platform_info, platform_folder)
        if logo_path and logo_path.exists():
            try:
                # Use JSON dimensions for the image
                img = self._create_image_from_json(logo_path, logo_json, max_width=3*inch, max_height=2*inch)
                if img:
                    story.append(img)
                    story.append(Spacer(1, 20))
            except Exception as e:
                print(f"Warning: Could not add platform logo: {str(e)}")
        
        # Platform basic info
        info_data = []
        if platform_info.get('abbreviation'):
            info_data.append(['Abbreviation:', platform_info['abbreviation']])
        if platform_info.get('alternative_name'):
            info_data.append(['Alternative Name:', platform_info['alternative_name']])
        if platform_info.get('platform_type', {}).get('name'):
            info_data.append(['Type:', platform_info['platform_type']['name']])
        if platform_info.get('url'):
            info_data.append(['IGDB URL:', platform_info['url']])
        
        if info_data:
            table = Table(info_data, colWidths=[1.5*inch, 4*inch])
            table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(table)
            story.append(Spacer(1, 20))
        
        # Platform versions/descriptions
        versions = platform_info.get('versions', [])
        if versions:
            story.append(Paragraph("Platform Versions", self.styles['SectionHeader']))
            for version in versions:
                if version.get('name'):
                    story.append(Paragraph(f"<b>{version['name']}</b>", self.styles['GameInfo']))
                
                # Add release dates and regions
                release_dates = version.get('platform_version_release_dates', [])
                if release_dates:
                    story.append(Paragraph("<b>Release Information:</b>", self.styles['GameInfo']))
                    for release in release_dates:
                        date_str = release.get('date', 'Unknown date')
                        # Format date to human-readable if it's in ISO format
                        if date_str != 'Unknown date':
                            try:
                                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                                date_str = self._format_human_readable_date(date_obj)
                            except:
                                pass  # Keep original date string if parsing fails
                        
                        region_info = release.get('release_region', {})
                        region_name = region_info.get('region', 'Unknown region')
                        # Format region name nicely
                        region_display = region_name.replace('_', ' ').title()
                        story.append(Paragraph(f"• {date_str} - {region_display}", self.styles['Normal']))
                    story.append(Spacer(1, 8))
                
                # Add platform logo if available
                platform_logo = version.get('platform_logo', {})
                if platform_logo and platform_logo.get('local_file_path'):
                    logo_path = platform_folder / platform_logo['local_file_path']
                    if logo_path.exists():
                        try:
                            # Use JSON dimensions for the image
                            logo_img = self._create_image_from_json(logo_path, platform_logo, max_width=3*inch, max_height=1.5*inch)
                            if logo_img:
                                story.append(logo_img)
                                story.append(Spacer(1, 10))
                        except Exception as e:
                            print(f"Warning: Could not add version logo: {str(e)}")
                
                if version.get('summary'):
                    # Process escaped characters and include full summary
                    summary = self._process_text(version['summary'])
                    story.append(Paragraph(summary, self.styles['PlatformInfo']))
                story.append(Spacer(1, 15))
    
    def _add_games_section(self, story, platform_folder):
        """Add games section to the story."""
        # Find all game folders
        game_folders = [f for f in platform_folder.iterdir() if f.is_dir()]
        
        if not game_folders:
            story.append(Paragraph("No games found for this platform.", self.styles['Normal']))
            return
        
        story.append(PageBreak())
        story.append(Paragraph("Games Library", self.styles['SectionHeader']))
        story.append(Spacer(1, 20))
        
        for game_folder in sorted(game_folders):
            game_json_file = game_folder / f"{game_folder.name}.json"
            if not game_json_file.exists():
                continue
            
            try:
                with open(game_json_file, 'r', encoding='utf-8') as f:
                    game_data = json.load(f)
                
                self._add_single_game(story, game_data, game_folder)
                
            except Exception as e:
                print(f"Warning: Could not process game {game_folder.name}: {str(e)}")
                continue
    
    def _add_single_game(self, story, game_data, game_folder):
        """Add a single game to the story."""
        game_name = game_data.get('name', game_folder.name)
        story.append(Paragraph(game_name, self.styles['GameTitle']))
        
        # Game cover image (if available)
        cover_path, cover_json = self._find_game_cover_with_json(game_data, game_folder)
        
        # Create a table with image on left and info on right
        table_data = []
        
        # Prepare game info text
        info_parts = []
        
        if game_data.get('first_release_date'):
            try:
                # Convert timestamp to human-readable date
                timestamp = int(game_data['first_release_date'])
                date_str = self._format_human_readable_date(datetime.fromtimestamp(timestamp))
                info_parts.append(f"<b>Release Date:</b> {date_str}")
            except:
                # Try to parse as ISO date string
                try:
                    date_obj = datetime.strptime(game_data['first_release_date'], '%Y-%m-%d')
                    date_str = self._format_human_readable_date(date_obj)
                    info_parts.append(f"<b>Release Date:</b> {date_str}")
                except:
                    info_parts.append(f"<b>Release Date:</b> {game_data['first_release_date']}")
        
        # Genres
        genres = game_data.get('genres', [])
        if genres:
            genre_names = [g.get('name', '') for g in genres if g.get('name')]
            if genre_names:
                info_parts.append(f"<b>Genres:</b> {', '.join(genre_names)}")
        
        # Companies (developers/publishers)
        companies = game_data.get('involved_companies', [])
        developers = []
        publishers = []
        for company in companies:
            company_info = company.get('company', {})
            company_name = company_info.get('name', '')
            if company_name:
                if company.get('developer'):
                    developers.append(company_name)
                if company.get('publisher'):
                    publishers.append(company_name)
        
        if developers:
            info_parts.append(f"<b>Developer:</b> {', '.join(developers)}")
        if publishers:
            info_parts.append(f"<b>Publisher:</b> {', '.join(publishers)}")
        
        # Game modes
        game_modes = game_data.get('game_modes', [])
        if game_modes:
            mode_names = [m.get('name', '') for m in game_modes if m.get('name')]
            if mode_names:
                info_parts.append(f"<b>Game Modes:</b> {', '.join(mode_names)}")
        
        # Themes
        themes = game_data.get('themes', [])
        if themes:
            theme_names = [t.get('name', '') for t in themes if t.get('name')]
            if theme_names:
                info_parts.append(f"<b>Themes:</b> {', '.join(theme_names)}")
        
        # Rating information
        if game_data.get('rating'):
            rating = round(game_data['rating'], 1)
            rating_count = game_data.get('rating_count', 0)
            if rating_count > 0:
                info_parts.append(f"<b>Rating:</b> {rating}/100 ({rating_count} votes)")
            else:
                info_parts.append(f"<b>Rating:</b> {rating}/100")
        
        # Summary
        if game_data.get('summary'):
            # Process escaped characters and include full summary
            summary = self._process_text(game_data['summary'])
            info_parts.append(f"<b>Description:</b> {summary}")
        
        info_text = '<br/>'.join(info_parts)
        
        # Create table row
        if cover_path and cover_path.exists():
            try:
                cover_img = self._create_image_from_json(cover_path, cover_json, max_width=1.5*inch, max_height=2*inch)
                if cover_img:
                    table_data = [[cover_img, Paragraph(info_text, self.styles['GameInfo'])]]
                else:
                    table_data = [['', Paragraph(info_text, self.styles['GameInfo'])]]
            except Exception as e:
                print(f"Warning: Could not add cover for {game_name}: {str(e)}")
                table_data = [['', Paragraph(info_text, self.styles['GameInfo'])]]
        else:
            table_data = [['', Paragraph(info_text, self.styles['GameInfo'])]]
        
        if table_data:
            table = Table(table_data, colWidths=[1.8*inch, 4.2*inch])
            table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ]))
            story.append(table)
        
        story.append(Spacer(1, 15))
    
    def _create_image_from_json(self, image_path, image_json, max_width, max_height):
        """Create a ReportLab image using dimensions from JSON data, properly constrained to max bounds."""
        if not image_json:
            # Fallback to old method if no JSON data
            return self._resize_image_for_pdf(image_path, max_width, max_height)
        
        try:
            # Get dimensions from JSON
            json_width = image_json.get('width', 0)
            json_height = image_json.get('height', 0)
            
            if json_width <= 0 or json_height <= 0:
                # Fallback to old method if invalid dimensions
                return self._resize_image_for_pdf(image_path, max_width, max_height)
            
            # Calculate aspect ratio from JSON dimensions
            aspect_ratio = json_width / json_height
            
            # Calculate scaled dimensions to fit within max bounds while preserving aspect ratio
            # Always ensure we don't exceed the maximum bounds
            width_constrained_height = max_width / aspect_ratio
            height_constrained_width = max_height * aspect_ratio
            
            if width_constrained_height <= max_height:
                # Width is the limiting factor
                scaled_width = max_width
                scaled_height = width_constrained_height
            else:
                # Height is the limiting factor
                scaled_width = height_constrained_width
                scaled_height = max_height
            
            # Ensure we don't exceed bounds (safety check)
            scaled_width = min(scaled_width, max_width)
            scaled_height = min(scaled_height, max_height)
            
            # Open and process the image
            with Image.open(image_path) as img:
                # Calculate pixel dimensions for resizing with higher DPI for better quality
                # Use 150 DPI instead of 72 for better image quality in PDFs
                dpi_factor = 150 / 72  # ~2x resolution for better quality
                pixel_width = int(scaled_width * 150 / inch)
                pixel_height = int(scaled_height * 150 / inch)
                
                # Resize image to calculated pixel dimensions using high-quality resampling
                resized_img = img.resize((pixel_width, pixel_height), Image.Resampling.LANCZOS)
                
                # Handle transparency properly
                if resized_img.mode in ('RGBA', 'LA') or 'transparency' in resized_img.info:
                    # For images with transparency, save as PNG to preserve alpha channel
                    img_buffer = io.BytesIO()
                    resized_img.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                else:
                    # For images without transparency, convert to RGB and save as PNG
                    if resized_img.mode in ('P', 'L'):
                        resized_img = resized_img.convert('RGB')
                    img_buffer = io.BytesIO()
                    resized_img.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                
                # Create ReportLab Image with calculated point dimensions
                return RLImage(img_buffer, width=scaled_width, height=scaled_height)
                
        except Exception as e:
            print(f"Error processing image with JSON dimensions {image_path}: {str(e)}")
            # Fallback to old method
            return self._resize_image_for_pdf(image_path, max_width, max_height)
    
    def _find_platform_logo_with_json(self, platform_info, platform_folder):
        """Find the platform logo file and return both path and JSON data."""
        # Look for local_file_path in platform versions
        versions = platform_info.get('versions', [])
        for version in versions:
            platform_logo = version.get('platform_logo', {})
            if platform_logo.get('local_file_path'):
                logo_path = platform_folder / platform_logo['local_file_path']
                if logo_path.exists():
                    return logo_path, platform_logo
        
        # Fallback: look for any platform logo file in the folder
        for file in platform_folder.glob("*platform_logo*"):
            if file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']:
                return file, None
        
        return None, None
    
    def _find_platform_logo(self, platform_info, platform_folder):
        """Find the platform logo file."""
        logo_path, _ = self._find_platform_logo_with_json(platform_info, platform_folder)
        return logo_path
    
    def _find_game_cover_with_json(self, game_data, game_folder):
        """Find the game cover image file and return both path and JSON data."""
        cover_info = game_data.get('cover', {})
        if cover_info.get('local_file_path'):
            cover_path = game_folder / cover_info['local_file_path']
            if cover_path.exists():
                return cover_path, cover_info
        
        # Fallback: look for any cover file in the folder
        for file in game_folder.glob("cover_*"):
            if file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']:
                return file, None
        
        return None, None
    
    def _find_game_cover(self, game_data, game_folder):
        """Find the game cover image file."""
        cover_path, _ = self._find_game_cover_with_json(game_data, game_folder)
        return cover_path
    
    def _resize_image_for_pdf(self, image_path, max_width, max_height):
        """Resize an image to fit within the specified dimensions while maintaining aspect ratio."""
        try:
            # Open and get image dimensions
            with Image.open(image_path) as img:
                # Calculate scaling factor
                width_ratio = max_width / img.width
                height_ratio = max_height / img.height
                scale_factor = min(width_ratio, height_ratio)
                
                # Calculate new dimensions
                new_width = img.width * scale_factor
                new_height = img.height * scale_factor
                
                # Calculate high-resolution pixel dimensions for better quality
                # Use 150 DPI instead of 72 for sharper images
                pixel_width = int(new_width * 150 / 72)
                pixel_height = int(new_height * 150 / 72)
                
                # Resize image with high-quality resampling
                resized_img = img.resize((pixel_width, pixel_height), Image.Resampling.LANCZOS)
                
                # Handle transparency properly
                if resized_img.mode in ('RGBA', 'LA') or 'transparency' in resized_img.info:
                    # For images with transparency, save as PNG to preserve alpha channel
                    img_buffer = io.BytesIO()
                    resized_img.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                else:
                    # For images without transparency, convert to RGB and save as PNG
                    if resized_img.mode in ('P', 'L'):
                        resized_img = resized_img.convert('RGB')
                    img_buffer = io.BytesIO()
                    resized_img.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                
                # Create ReportLab Image
                return RLImage(img_buffer, width=new_width, height=new_height)
                
        except Exception as e:
            print(f"Error processing image {image_path}: {str(e)}")
            return None
    
    def _process_text(self, text):
        """Process text to handle escaped characters and clean for PDF output, preserving Unicode."""
        if not text:
            return ""
        
        # Handle common escaped characters
        text = text.replace('\\n', '<br/>')  # Convert newlines to HTML breaks
        text = text.replace('\\t', ' ')      # Convert tabs to spaces
        text = text.replace('\\r', '')       # Remove carriage returns
        text = text.replace('\\"', '"')      # Unescape quotes
        text = text.replace("\\'", "'")      # Unescape single quotes
        text = text.replace('\\\\', '\\')    # Unescape backslashes
        
        # Handle actual newline characters that might be in the JSON
        text = text.replace('\n', '<br/>')
        text = text.replace('\r', '')
        
        # Clean up multiple spaces (preserve Unicode characters)
        import re
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def _format_human_readable_date(self, date_obj):
        """Format a datetime object to human-readable format like '20th December 1991'."""
        def get_ordinal_suffix(day):
            """Get the ordinal suffix for a day (st, nd, rd, th)."""
            if 10 <= day % 100 <= 20:
                return 'th'
            else:
                return {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
        
        day = date_obj.day
        month = date_obj.strftime('%B')  # Full month name
        year = date_obj.year
        
        ordinal_day = f"{day}{get_ordinal_suffix(day)}"
        return f"{ordinal_day} {month} {year}"
    
    def _sanitize_filename(self, filename):
        """Sanitize a filename for filesystem safety."""
        # Remove or replace problematic characters
        import re
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'[^\w\s-]', '', filename).strip()
        filename = re.sub(r'[-\s]+', '_', filename)
        return filename[:50]  # Limit length
    
    def generate_catalogues_for_all_platforms(self, detail_folder, output_folder):
        """
        Generate catalogues for all platforms in the detail folder.
        
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
