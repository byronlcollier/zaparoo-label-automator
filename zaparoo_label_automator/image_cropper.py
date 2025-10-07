"""
Image cropper module for automatically cropping transparent areas from images.
"""
from pathlib import Path
from PIL import Image
import numpy as np


class ImageCropper:
    """Handles automatic cropping of transparent areas from images."""
    
    @staticmethod
    def crop_transparent_borders(image_path):
        """
        Crop transparent/blank areas from the borders of an image.
        
        This method dynamically calculates the crop box by finding the bounding box
        of all non-transparent pixels. Preserves all transparency and alpha channel
        information in the remaining image.
        
        Args:
            image_path (Path): Path to the image file to crop
            
        Returns:
            bool: True if image was cropped (modified), False if no cropping was needed
            
        Raises:
            Exception: If image processing fails
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        try:
            # Open image and ensure it has an alpha channel
            with Image.open(image_path) as img:
                # Convert to RGBA if it doesn't have alpha channel
                if img.mode not in ('RGBA', 'LA'):
                    # Check if the image has a transparency palette
                    if 'transparency' in img.info:
                        img = img.convert('RGBA')
                    else:
                        # No transparency information, no cropping needed
                        return False
                else:
                    # Make a copy to avoid modifying the original while it's open
                    img = img.copy()
            
            # Get the bounding box of non-transparent pixels
            bbox = ImageCropper._get_non_transparent_bbox(img)
            
            if bbox is None:
                # Image is completely transparent, no cropping needed
                return False
            
            # Check if cropping is actually needed
            if bbox == (0, 0, img.width, img.height):
                # No transparent borders to crop
                return False
            
            # Crop the image to the bounding box
            cropped_img = img.crop(bbox)
            
            # Save the cropped image back to the same file
            # Preserve the original format and quality
            save_kwargs = {}
            
            # Determine format from file extension
            file_format = img.format or ImageCropper._format_from_extension(image_path)
            
            # Handle format-specific save parameters
            if file_format.upper() == 'PNG':
                save_kwargs['optimize'] = True
                save_kwargs['format'] = 'PNG'
            elif file_format.upper() == 'WEBP':
                save_kwargs['format'] = 'WEBP'
                save_kwargs['lossless'] = True  # Preserve quality for WEBP
                save_kwargs['method'] = 6  # Best compression
            else:
                save_kwargs['format'] = file_format
            
            cropped_img.save(image_path, **save_kwargs)
            
            return True
            
        except Exception as e:
            raise Exception(f"Failed to crop image {image_path}: {str(e)}")
    
    @staticmethod
    def _get_non_transparent_bbox(img):
        """
        Calculate the bounding box of all non-transparent pixels.
        
        Args:
            img (PIL.Image): Image with alpha channel
            
        Returns:
            tuple or None: (left, top, right, bottom) bounding box, or None if all pixels are transparent
        """
        # Convert to numpy array for efficient processing
        img_array = np.array(img)
        
        # Handle different image modes
        if img.mode == 'RGBA':
            # For RGBA, check the alpha channel (index 3)
            alpha_channel = img_array[:, :, 3]
        elif img.mode == 'LA':
            # For LA (grayscale + alpha), check the alpha channel (index 1)
            alpha_channel = img_array[:, :, 1]
        else:
            # Should not happen given our pre-processing, but handle gracefully
            return None
        
        # Find all non-transparent pixels (alpha > 0)
        non_transparent_pixels = alpha_channel > 0
        
        # Find the indices of non-transparent pixels
        non_transparent_coords = np.where(non_transparent_pixels)
        
        if len(non_transparent_coords[0]) == 0:
            # No non-transparent pixels found
            return None
        
        # Calculate bounding box
        top = int(np.min(non_transparent_coords[0]))
        bottom = int(np.max(non_transparent_coords[0])) + 1  # +1 because crop is exclusive
        left = int(np.min(non_transparent_coords[1]))
        right = int(np.max(non_transparent_coords[1])) + 1  # +1 because crop is exclusive
        
        return (left, top, right, bottom)
    
    @staticmethod
    def _format_from_extension(file_path):
        """
        Determine image format from file extension.
        
        Args:
            file_path (Path): Path to image file
            
        Returns:
            str: Image format (PNG, WEBP, etc.)
        """
        extension = file_path.suffix.lower()
        
        format_map = {
            '.png': 'PNG',
            '.webp': 'WEBP',
            '.jpg': 'JPEG',
            '.jpeg': 'JPEG',
            '.gif': 'GIF',
            '.bmp': 'BMP',
            '.tiff': 'TIFF',
            '.tif': 'TIFF'
        }
        
        return format_map.get(extension, 'PNG')  # Default to PNG
    
    @staticmethod
    def batch_crop_images(folder_path, file_patterns=None):
        """
        Crop all images in a folder that match the specified patterns.
        
        Args:
            folder_path (Path): Path to folder containing images
            file_patterns (list, optional): List of glob patterns to match. 
                                          Defaults to ['*.png', '*.webp']
            
        Returns:
            dict: Results with keys 'processed', 'cropped', 'errors'
        """
        folder_path = Path(folder_path)
        
        if not folder_path.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")
        
        if file_patterns is None:
            file_patterns = ['*.png', '*.webp']
        
        results = {
            'processed': 0,
            'cropped': 0,
            'errors': []
        }
        
        # Find all matching image files
        image_files = []
        for pattern in file_patterns:
            image_files.extend(folder_path.glob(pattern))
        
        for image_file in image_files:
            try:
                results['processed'] += 1
                
                if ImageCropper.crop_transparent_borders(image_file):
                    results['cropped'] += 1
                    
            except Exception as e:
                results['errors'].append(f"Error processing {image_file.name}: {str(e)}")
        
        return results