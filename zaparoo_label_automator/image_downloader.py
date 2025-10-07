"""
Image downloader module for downloading images from IGDB.
"""
import json
import requests
from pathlib import Path
from zaparoo_label_automator.image_cropper import ImageCropper


class ImageDownloader:
    """Downloads images from IGDB based on game data."""
    
    def __init__(self, config_path, media_config=None):
        """Initialize with image configuration."""
        self.config_path = config_path
        self.config = self._load_config()
        self.session = requests.Session()
        # Set a reasonable timeout for image downloads
        self.timeout = 30
        self.media_config = media_config or {}
    
    def _load_config(self):
        """Load image configuration from JSON file."""
        config_file = Path(self.config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Image config file not found: {self.config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def find_image_objects(self, game_data):
        """
        Find image objects in game data based on enabled media types.
        
        Args:
            game_data (dict): The game data from IGDB API
            
        Returns:
            list: List of tuples (parent_name, image_object)
        """
        images = []
        
        # Process each enabled media type
        for media_type, enabled in self.media_config.items():
            if enabled and media_type != 'game_video':  # Skip video for now
                self._extract_images_from_field(game_data, media_type, images)
        
        return images
    
    def find_all_image_objects(self, data):
        """
        Find ALL image objects in data regardless of media configuration.
        This recursively searches through the entire data structure for any object with an 'image_id' field.
        
        Args:
            data (dict): The data from IGDB API
            
        Returns:
            list: List of tuples (field_name, image_object)
        """
        images = []
        self._recursive_extract_all_images(data, images)
        return images
    
    def _extract_images_from_field(self, game_data, field_name, images):
        """Extract images from a specific field in game data."""
        # Try both singular and plural forms of the field name
        possible_field_names = [field_name]
        if field_name.endswith('s'):
            possible_field_names.append(field_name[:-1])  # Remove 's'
        else:
            possible_field_names.append(field_name + 's')  # Add 's'
        
        for possible_name in possible_field_names:
            if possible_name in game_data:
                field_data = game_data[possible_name]
                
                # Handle single image object
                if isinstance(field_data, dict) and self._is_image_object(field_data):
                    images.append((field_name, field_data))
                
                # Handle array of image objects
                elif isinstance(field_data, list):
                    for item in field_data:
                        if isinstance(item, dict) and self._is_image_object(item):
                            images.append((field_name, item))
                
                # Handle nested objects (like platform_logo within versions)
                elif isinstance(field_data, dict):
                    self._extract_nested_images(field_data, field_name, images)
                elif isinstance(field_data, list):
                    for item in field_data:
                        if isinstance(item, dict):
                            self._extract_nested_images(item, field_name, images)
                
                return  # Found the field, no need to try other variants
    
    def _extract_nested_images(self, obj, parent_field, images):
        """Extract images from nested objects (e.g., platform_logo in versions)."""
        for key, value in obj.items():
            if isinstance(value, dict) and self._is_image_object(value):
                images.append((key, value))
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        for nested_key, nested_value in item.items():
                            if isinstance(nested_value, dict) and self._is_image_object(nested_value):
                                images.append((nested_key, nested_value))
    
    def _is_image_object(self, obj):
        """
        Check if an object represents an image.
        
        Args:
            obj (dict): Object to check
            
        Returns:
            bool: True if object contains image fields
        """
        # For the "find all images" functionality, we only need image_id
        # The original logic requires width/height too, but we'll be more lenient for finding all
        return isinstance(obj, dict) and 'image_id' in obj
    
    def _recursive_extract_all_images(self, data, images, parent_path=""):
        """
        Recursively extract all image objects from data structure.
        
        Args:
            data: The data to search (dict, list, or other)
            images: List to append found images to
            parent_path: Current path in the data structure for context
        """
        if isinstance(data, dict):
            # Check if this dict is an image object
            if self._is_image_object(data):
                # Use the parent path or a generic name if at root
                field_name = parent_path if parent_path else "image"
                images.append((field_name, data))
            else:
                # Recursively search in all dict values
                for key, value in data.items():
                    new_path = f"{parent_path}_{key}" if parent_path else key
                    self._recursive_extract_all_images(value, images, new_path)
        
        elif isinstance(data, list):
            # Recursively search in all list items
            for i, item in enumerate(data):
                new_path = f"{parent_path}[{i}]" if parent_path else f"item[{i}]"
                self._recursive_extract_all_images(item, images, new_path)
    
    def build_image_url(self, image_type, image_id):
        """
        Build the complete image URL using direct mapping.
        
        Args:
            image_type (str): Type of image (e.g., 'cover', 'platform_logo')
            image_id (str): The image ID from IGDB API
            
        Returns:
            str: Complete URL for downloading the image
        """
        if image_type not in self.config['image_size_mapping']:
            raise ValueError(f"No size mapping found for image type: {image_type}")
        
        size_name = self.config['image_size_mapping'][image_type]
        
        # Build URL: base_url + size_name + image_id + file_format
        url_parts = [
            self.config['base_url'].rstrip('/'),
            size_name,
            image_id + self.config['file_format']
        ]
        
        return '/'.join(url_parts)
    
    def build_filename(self, parent_name, image_obj):
        """
        Build filename for an image based on parent name and image data.
        
        Args:
            parent_name (str): Name of the parent object (e.g., 'cover', 'artwork')
            image_obj (dict): Image object containing id and image_id
            
        Returns:
            str: Complete filename with extension
        """
        # Get the image ID and object ID
        image_id = image_obj['image_id']
        obj_id = image_obj.get('id', 'unknown')
        
        # Get file extension
        extension = self.config['file_format']
        
        # Build filename: parent_name + object_id + image_id + extension
        filename = f"{parent_name}_{obj_id}_{image_id}{extension}"
        
        # Sanitize filename
        return self._sanitize_filename(filename)
    
    def build_simple_filename(self, image_type, image_obj):
        """
        Build a simplified filename for an image: image_type + numeric_id + image_id + extension.
        
        Args:
            image_type (str): Type of image (e.g., 'cover', 'platform_logo', 'screenshot')
            image_obj (dict): Image object containing id and image_id
            
        Returns:
            str: Simple filename with extension
        """
        # Get the numeric ID and image ID
        numeric_id = image_obj.get('id', 'unknown')
        image_id = image_obj['image_id']
        
        # Get file extension
        extension = self.config['file_format']
        
        # Build simple filename: image_type + numeric_id + image_id + extension
        filename = f"{image_type}_{numeric_id}_{image_id}{extension}"
        
        # Sanitize filename
        return self._sanitize_filename(filename)
    
    def _sanitize_filename(self, filename):
        """Make filename filesystem-safe."""
        import re
        # Remove or replace characters not allowed in filenames
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove multiple consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        return sanitized
    
    def download_image(self, url, filepath):
        """
        Download an image from URL to filepath and automatically crop transparent borders.
        
        Args:
            url (str): URL to download from
            filepath (Path): Path where to save the image
            
        Raises:
            Exception: If download fails
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Ensure parent directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Write image data
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            # Automatically crop transparent borders from the downloaded image
            try:
                cropped = ImageCropper.crop_transparent_borders(filepath)
                if cropped:
                    print(f"  Cropped transparent borders from {filepath.name}")
            except Exception as crop_error:
                # Log the cropping error but don't fail the download
                print(f"  Warning: Could not crop {filepath.name}: {str(crop_error)}")
                
        except requests.RequestException as e:
            raise Exception(f"Failed to download image from {url}: {str(e)}")
        except IOError as e:
            raise Exception(f"Failed to write image to {filepath}: {str(e)}")
    
    def download_all_images(self, game_data, output_folder):
        """
        Download all images found in game data to the specified folder.
        
        Args:
            game_data (dict): Game data from IGDB API
            output_folder (Path): Folder where to save images
            
        Returns:
            dict: Mapping of image_id to relative file path for downloaded images
            
        Raises:
            Exception: If any image download fails
        """
        images = self.find_image_objects(game_data)
        
        if not images:
            return {}
        
        downloaded_files = {}
        
        for parent_name, image_obj in images:
            try:
                # Build image URL using direct mapping
                url = self.build_image_url(parent_name, image_obj['image_id'])
                
                # Build filename
                filename = self.build_filename(parent_name, image_obj)
                filepath = output_folder / filename
                
                # Download image
                self.download_image(url, filepath)
                
                # Store the relative path for this image_id
                downloaded_files[image_obj['image_id']] = filename
                
            except Exception as e:
                # Re-raise with more context as per requirements
                raise Exception(f"Failed to download image {image_obj.get('image_id', 'unknown')} "
                              f"for {parent_name}: {str(e)}")
        
        return downloaded_files
    
    def download_all_images_recursive(self, data, output_folder):
        """
        Download images found in data to the specified folder.
        Respects media configuration to selectively download enabled image types.
        
        Args:
            data (dict): Data from IGDB API
            output_folder (Path): Folder where to save images
            
        Returns:
            dict: Mapping of image_id to relative file path for downloaded images
            
        Raises:
            Exception: If any image download fails
        """
        images = self.find_all_image_objects(data)
        
        if not images:
            return {}
        
        downloaded_files = {}
        
        for parent_name, image_obj in images:
            try:
                # Determine image type from parent name
                image_type = self._determine_image_type(parent_name)
                
                # Check if this image type is enabled in media config
                if not self.media_config.get(image_type, False):
                    continue  # Skip disabled image types
                
                # Build image URL
                url = self.build_image_url(image_type, image_obj['image_id'])
                
                # Build simplified filename
                filename = self.build_simple_filename(image_type, image_obj)
                filepath = output_folder / filename
                
                # Download image
                self.download_image(url, filepath)
                
                # Store the relative path for this image_id
                downloaded_files[image_obj['image_id']] = filename
                
            except Exception as e:
                # Re-raise with more context as per requirements
                raise Exception(f"Failed to download image {image_obj.get('image_id', 'unknown')} "
                              f"for {parent_name}: {str(e)}")
        
        return downloaded_files
    
    def _determine_image_type(self, parent_name):
        """
        Determine the image type from the parent field name for URL building and media config filtering.
        
        Args:
            parent_name (str): The field name where the image was found
            
        Returns:
            str: The image type to use for URL building and media config checking
        """
        parent_lower = parent_name.lower()
        
        # Map field patterns to media config keys (which should match URL building types)
        if 'cover' in parent_lower:
            return 'cover'
        elif 'logo' in parent_lower or 'platform' in parent_lower:
            return 'platform_logo'
        elif 'screenshot' in parent_lower:
            return 'screenshot'
        elif 'artwork' in parent_lower:
            return 'artwork'
        else:
            # Default fallback - most unknown images are treated as screenshots
            return 'screenshot'
    
    def add_local_file_paths(self, data, downloaded_files):
        """
        Add local file paths to image objects in the data structure.
        
        Args:
            data (dict): The JSON data structure to modify
            downloaded_files (dict): Mapping of image_id to relative file path
            
        Returns:
            dict: Modified data structure with local_file_path added to image objects
        """
        if isinstance(data, dict):
            # Create a copy to avoid modifying the original
            modified_data = {}
            for key, value in data.items():
                if key == 'image_id' and value in downloaded_files:
                    # This is an image object that was downloaded
                    modified_data[key] = value
                    # Add the local file path
                    modified_data['local_file_path'] = downloaded_files[value]
                else:
                    # Recursively process nested structures
                    modified_data[key] = self.add_local_file_paths(value, downloaded_files)
            return modified_data
        elif isinstance(data, list):
            # Process each item in the list
            return [self.add_local_file_paths(item, downloaded_files) for item in data]
        else:
            # Return primitive values unchanged
            return data