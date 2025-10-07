"""
Label generator module for creating Zaparoo labels from SVG templates.
"""
import json
import shutil
from pathlib import Path
from xml.etree import ElementTree as ET
from PIL import Image, ImageDraw
import cairosvg
import io
from zaparoo_label_automator.platform_logo_selector import PlatformLogoSelector


class LabelGenerator:
    """Generates labels by substituting images in SVG templates and converting to PNG/PDF."""
    
    def __init__(self, template_path, dpi=300, output_formats=None):
        """
        Initialize the label generator.
        
        Args:
            template_path (str): Path to the SVG template file
            dpi (int): DPI for output image conversion (default: 300)
            output_formats (list): List of output formats to generate (default: ['png', 'pdf'])
                                 Supported formats: 'png', 'pdf'
        """
        self.template_path = Path(template_path)
        self.dpi = dpi
        self.output_formats = output_formats or ['png', 'pdf']
        
        if not self.template_path.exists():
            raise FileNotFoundError(f"SVG template not found: {template_path}")
    
    def generate_labels_from_catalogue(self, catalogue_json_path, reference_data_path, label_output_folder):
        """
        Generate labels for games specified in the catalogue JSON.
        
        Args:
            catalogue_json_path (Path): Path to catalogue JSON file
            reference_data_path (Path): Path to reference data folder
            label_output_folder (Path): Path to output folder for labels
            
        Returns:
            int: Number of labels generated
        """
        catalogue_json_path = Path(catalogue_json_path)
        reference_data_path = Path(reference_data_path)
        label_output_folder = Path(label_output_folder)
        
        if not catalogue_json_path.exists():
            raise FileNotFoundError(f"Catalogue JSON not found: {catalogue_json_path}")
        
        # Load catalogue data
        with open(catalogue_json_path, 'r', encoding='utf-8') as f:
            catalogue_data = json.load(f)
        
        # Create output folder
        label_output_folder.mkdir(parents=True, exist_ok=True)
        
        total_labels_generated = 0
        
        # Process each platform in the catalogue
        for platform_name, platform_data in catalogue_data['platforms'].items():
            print(f"Generating labels for {platform_name}...")
            
            platform_folder = reference_data_path / platform_data['platform_folder']
            if not platform_folder.exists():
                print(f"Warning: Platform folder not found: {platform_folder}")
                continue
            
            # Read platform info for logo
            platform_info_file = platform_folder / 'platform_info.json'
            if not platform_info_file.exists():
                print(f"Warning: No platform_info.json found in {platform_folder}")
                continue
            
            with open(platform_info_file, 'r', encoding='utf-8') as f:
                platform_info = json.load(f)
            
            # Find platform logo
            platform_logo_path = self._find_platform_logo(platform_info, platform_folder)
            
            # Generate labels for selected games only
            platform_labels_generated = 0
            for game_info in platform_data['games']:
                game_folder_path = reference_data_path / game_info['game_folder_path']
                if game_folder_path.exists():
                    success = self._generate_game_label(game_folder_path, platform_logo_path, label_output_folder)
                    if success:
                        platform_labels_generated += 1
                else:
                    print(f"Warning: Game folder not found: {game_folder_path}")
            
            print(f"Generated {platform_labels_generated} labels for {platform_name}")
            total_labels_generated += platform_labels_generated
        
        return total_labels_generated

    def generate_labels_for_platform(self, platform_folder, label_output_folder=None):
        """
        Generate labels for all games in a platform folder.
        
        Args:
            platform_folder (Path): Path to platform folder containing games
            label_output_folder (Path, optional): Path to output folder for labels. If None, uses game folders.
        """
        platform_folder = Path(platform_folder)
        
        if not platform_folder.exists():
            raise FileNotFoundError(f"Platform folder not found: {platform_folder}")
        
        # Read platform info
        platform_info_file = platform_folder / 'platform_info.json'
        if not platform_info_file.exists():
            print(f"Warning: No platform_info.json found in {platform_folder}")
            return
        
        with open(platform_info_file, 'r', encoding='utf-8') as f:
            platform_info = json.load(f)
        
        # Find platform logo
        platform_logo_path = self._find_platform_logo(platform_info, platform_folder)
        
        # Create label output folder if specified
        if label_output_folder:
            label_output_folder = Path(label_output_folder)
            label_output_folder.mkdir(parents=True, exist_ok=True)
        
        # Process each game subfolder
        labels_generated = 0
        for game_folder in platform_folder.iterdir():
            if game_folder.is_dir():
                output_folder = label_output_folder if label_output_folder else game_folder
                success = self._generate_game_label(game_folder, platform_logo_path, output_folder)
                if success:
                    labels_generated += 1
        
        print(f"Generated {labels_generated} labels for {platform_folder.name}")
    
    def _find_platform_logo(self, platform_info, platform_folder):
        """
        Find the best platform logo file path using selection logic.
        
        Args:
            platform_info (dict): Platform information from JSON
            platform_folder (Path): Platform folder path
            
        Returns:
            Path or None: Path to platform logo file
        """
        logo_path = PlatformLogoSelector.find_platform_logo_path(platform_info, platform_folder)
        if not logo_path:
            print(f"Warning: No platform logo found for {platform_folder.name}")
        return logo_path
    

    
    def _generate_game_label(self, game_folder, platform_logo_path, output_folder=None):
        """
        Generate label for a single game.
        
        Args:
            game_folder (Path): Path to game folder
            platform_logo_path (Path or None): Path to platform logo file
            output_folder (Path or None): Path to output folder for labels. If None, uses game_folder.
        """
        # Find game JSON file
        json_files = list(game_folder.glob('*.json'))
        if not json_files:
            print(f"Warning: No JSON file found in {game_folder}")
            return
        
        game_json_file = json_files[0]
        
        with open(game_json_file, 'r', encoding='utf-8') as f:
            game_data = json.load(f)
        
        # Find cover image
        cover_path = self._find_cover_image(game_data, game_folder)
        if not cover_path:
            print(f"Warning: No cover image found for {game_folder.name}")
            return False
        
        # Get platform name from parent folder
        platform_name = game_folder.parent.name
        
        # Use specified output folder or default to game folder
        label_output_folder = output_folder if output_folder else game_folder
        
        # Generate label
        try:
            self._create_label(
                label_output_folder,
                cover_path,
                platform_logo_path,
                game_data.get('name', game_folder.name),
                platform_name
            )
            return True
        except Exception as e:
            print(f"Error generating label for {game_folder.name}: {str(e)}")
            return False
    
    def _find_cover_image(self, game_data, game_folder):
        """
        Find the cover image file path.
        
        Args:
            game_data (dict): Game data from JSON
            game_folder (Path): Game folder path
            
        Returns:
            Path or None: Path to cover image file
        """
        # Look for cover in game data
        cover = game_data.get('cover', {})
        local_file_path = cover.get('local_file_path')
        if local_file_path:
            cover_path = game_folder / local_file_path
            if cover_path.exists():
                return cover_path
        
        # Fallback: look for any webp file that might be cover
        for file_path in game_folder.glob('cover_*.webp'):
            return file_path
        
        return None
    
    def _create_label(self, output_folder, cover_path, platform_logo_path, game_name, platform_name):
        """
        Create label by substituting images in SVG template and converting to PNG/PDF.
        
        Args:
            output_folder (Path): Path to folder for label output
            cover_path (Path): Path to cover image
            platform_logo_path (Path or None): Path to platform logo
            game_name (str): Name of the game for filename
            platform_name (str): Name of the platform for filename prefix
        """
        # Read and parse SVG template
        with open(self.template_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        
        # Register XML namespaces
        ET.register_namespace('', 'http://www.w3.org/2000/svg')
        ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
        
        # Parse SVG as XML
        try:
            root = ET.fromstring(svg_content)
        except ET.ParseError as e:
            raise Exception(f"Failed to parse SVG template: {str(e)}")
        
        # Find placeholder elements
        cover_placeholder = self._find_element_by_id(root, 'cover-placeholder')
        platform_placeholder = self._find_element_by_id(root, 'platform_logo-placeholder')
        
        # Substitute images
        if cover_placeholder is not None:
            self._substitute_image(root, cover_placeholder, cover_path, 'center')
        
        if platform_placeholder is not None and platform_logo_path:
            self._substitute_image(root, platform_placeholder, platform_logo_path, 'center')
        
        # Convert modified SVG to string with proper XML declaration
        modified_svg = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding='unicode')
        
        # Generate output files with platform prefix and no spaces
        sanitized_platform = self._sanitize_filename(platform_name)
        sanitized_game = self._sanitize_filename(game_name)
        filename_base = f"{sanitized_platform}_{sanitized_game}_label"
        
        # Generate specified output formats
        if 'png' in self.output_formats:
            png_path = output_folder / f"{filename_base}.png"
            self._svg_to_png(modified_svg, png_path)
        
        if 'pdf' in self.output_formats:
            pdf_path = output_folder / f"{filename_base}.pdf"
            self._svg_to_pdf(modified_svg, pdf_path)
    
    def _find_element_by_id(self, root, element_id):
        """
        Find an element by its ID attribute.
        
        Args:
            root: XML root element
            element_id (str): ID to search for
            
        Returns:
            Element or None: Found element
        """
        # Handle namespaces in SVG by searching all elements
        for elem in root.iter():
            if elem.get('id') == element_id:
                return elem
        return None
    
    def _substitute_image(self, root, placeholder, image_path, alignment):
        """
        Substitute placeholder with actual image, preserving aspect ratio.
        
        Args:
            root: XML root element
            placeholder: Placeholder element to replace
            image_path (Path): Path to image file
            alignment (str): Image alignment ('center' or 'left-middle')
        """
        # Get placeholder dimensions and position
        x = float(placeholder.get('x', 0))
        y = float(placeholder.get('y', 0))
        width = float(placeholder.get('width', 0))
        height = float(placeholder.get('height', 0))
        
        # Load image to get actual dimensions
        try:
            with Image.open(image_path) as img:
                img_width, img_height = img.size
        except Exception as e:
            raise Exception(f"Failed to load image {image_path}: {str(e)}")
        
        # Calculate scaled dimensions while preserving aspect ratio
        aspect_ratio = img_width / img_height
        placeholder_aspect = width / height
        
        if aspect_ratio > placeholder_aspect:
            # Image is wider than placeholder
            new_width = width
            new_height = width / aspect_ratio
        else:
            # Image is taller than placeholder
            new_width = height * aspect_ratio
            new_height = height
        
        # Calculate position based on alignment
        if alignment == 'left-middle':
            # Align to left edge, center vertically
            new_x = x
            new_y = y + (height - new_height) / 2
        else:
            # Default: center both horizontally and vertically
            new_x = x + (width - new_width) / 2
            new_y = y + (height - new_height) / 2
        
        # Create image element with proper SVG namespace
        image_elem = ET.Element('image')
        image_elem.set('x', str(new_x))
        image_elem.set('y', str(new_y))
        image_elem.set('width', str(new_width))
        image_elem.set('height', str(new_height))
        
        # Embed image as base64 data URL for better compatibility with CairoSVG
        data_url = self._create_data_url(image_path)
        image_elem.set('href', data_url)
        
        # Also set xlink:href for older SVG readers
        image_elem.set('{http://www.w3.org/1999/xlink}href', data_url)
        
        # Replace placeholder with image element
        parent = None
        for elem in root.iter():
            if placeholder in list(elem):
                parent = elem
                break
        
        if parent is not None:
            # Find index of placeholder and replace it
            children = list(parent)
            index = children.index(placeholder)
            parent.remove(placeholder)
            parent.insert(index, image_elem)
    
    def _svg_to_png(self, svg_content, output_path):
        """
        Convert SVG content to PNG file.
        
        Args:
            svg_content (str): SVG content as string
            output_path (Path): Output PNG file path
        """
        try:
            # Convert SVG to PNG using cairosvg
            png_data = cairosvg.svg2png(
                bytestring=svg_content.encode('utf-8'),
                dpi=self.dpi
            )
            
            # Write PNG file
            with open(output_path, 'wb') as f:
                f.write(png_data)
        except Exception as e:
            raise Exception(f"Failed to convert SVG to PNG: {str(e)}")
    
    def _svg_to_pdf(self, svg_content, output_path):
        """
        Convert SVG content to PDF file.
        
        Args:
            svg_content (str): SVG content as string
            output_path (Path): Output PDF file path
        """
        try:
            # Convert SVG to PDF using cairosvg
            pdf_data = cairosvg.svg2pdf(
                bytestring=svg_content.encode('utf-8'),
                dpi=self.dpi
            )
            
            # Write PDF file
            with open(output_path, 'wb') as f:
                f.write(pdf_data)
        except Exception as e:
            raise Exception(f"Failed to convert SVG to PDF: {str(e)}")
    
    def _create_data_url(self, image_path):
        """
        Create a base64 data URL from an image file.
        
        Args:
            image_path (Path): Path to image file
            
        Returns:
            str: Base64 data URL
        """
        import base64
        import mimetypes
        
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(str(image_path))
        if not mime_type:
            # Default to webp for .webp files
            if str(image_path).lower().endswith('.webp'):
                mime_type = 'image/webp'
            else:
                mime_type = 'image/png'
        
        # Read and encode image file
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        base64_data = base64.b64encode(image_data).decode('utf-8')
        return f"data:{mime_type};base64,{base64_data}"
    
    def _sanitize_filename(self, filename):
        """Make filename filesystem-safe."""
        import re
        # Remove or replace characters not allowed in filenames
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Replace spaces with underscores
        sanitized = sanitized.replace(' ', '_')
        # Remove multiple consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        return sanitized if sanitized else 'unknown'