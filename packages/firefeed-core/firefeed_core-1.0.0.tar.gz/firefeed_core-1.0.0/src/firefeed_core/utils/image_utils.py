"""
Image Utilities

Common image processing utilities for FireFeed microservices.
"""

import io
import logging
from typing import Optional, Tuple, Dict, Any
from PIL import Image, ImageOps, ExifTags
import hashlib
import os

logger = logging.getLogger(__name__)


def resize_image(image_data: bytes, max_width: int = 800, max_height: int = 600, 
                quality: int = 85) -> bytes:
    """
    Resize image to fit within specified dimensions while maintaining aspect ratio.
    
    Args:
        image_data: Raw image bytes
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels
        quality: JPEG quality (1-100)
        
    Returns:
        Resized image bytes
    """
    try:
        # Open image
        image = Image.open(io.BytesIO(image_data))
        
        # Handle EXIF orientation
        image = _fix_orientation(image)
        
        # Calculate new dimensions
        original_width, original_height = image.size
        ratio = min(max_width / original_width, max_height / original_height)
        
        if ratio < 1:
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
        
        # Save to bytes
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=quality, optimize=True)
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Error resizing image: {e}")
        raise ValueError(f"Failed to resize image: {e}")


def optimize_image(image_data: bytes, quality: int = 85, format: str = 'JPEG') -> bytes:
    """
    Optimize image by recompressing with specified quality.
    
    Args:
        image_data: Raw image bytes
        quality: Compression quality (1-100)
        format: Output format (JPEG, PNG, WEBP)
        
    Returns:
        Optimized image bytes
    """
    try:
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'P') and format.upper() == 'JPEG':
            image = image.convert('RGB')
        
        output = io.BytesIO()
        image.save(output, format=format.upper(), quality=quality, optimize=True)
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Error optimizing image: {e}")
        raise ValueError(f"Failed to optimize image: {e}")


def get_image_info(image_data: bytes) -> Dict[str, Any]:
    """
    Get image information including dimensions, format, and size.
    
    Args:
        image_data: Raw image bytes
        
    Returns:
        Dictionary with image information
    """
    try:
        image = Image.open(io.BytesIO(image_data))
        
        # Handle EXIF orientation
        image = _fix_orientation(image)
        
        width, height = image.size
        format_name = image.format
        mode = image.mode
        
        # Calculate aspect ratio
        aspect_ratio = width / height if height > 0 else 0
        
        return {
            'width': width,
            'height': height,
            'format': format_name,
            'mode': mode,
            'aspect_ratio': aspect_ratio,
            'size_bytes': len(image_data),
            'size_mb': len(image_data) / (1024 * 1024)
        }
        
    except Exception as e:
        logger.error(f"Error getting image info: {e}")
        raise ValueError(f"Failed to get image info: {e}")


def validate_image(image_data: bytes, max_size_mb: float = 10.0, 
                  allowed_formats: Optional[list] = None) -> bool:
    """
    Validate image data.
    
    Args:
        image_data: Raw image bytes
        max_size_mb: Maximum file size in MB
        allowed_formats: List of allowed formats
        
    Returns:
        True if image is valid, False otherwise
    """
    try:
        if not image_data:
            return False
        
        # Check file size
        size_mb = len(image_data) / (1024 * 1024)
        if size_mb > max_size_mb:
            logger.warning(f"Image size {size_mb:.2f}MB exceeds limit of {max_size_mb}MB")
            return False
        
        # Try to open image
        image = Image.open(io.BytesIO(image_data))
        
        # Check format
        if allowed_formats and image.format not in allowed_formats:
            logger.warning(f"Image format {image.format} not allowed")
            return False
        
        # Check dimensions
        width, height = image.size
        if width <= 0 or height <= 0:
            logger.warning("Invalid image dimensions")
            return False
        
        # Check aspect ratio (not too extreme)
        aspect_ratio = width / height if height > 0 else 0
        if aspect_ratio > 10 or aspect_ratio < 0.1:
            logger.warning(f"Extreme aspect ratio: {aspect_ratio}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating image: {e}")
        return False


def convert_image_format(image_data: bytes, target_format: str, quality: int = 85) -> bytes:
    """
    Convert image to different format.
    
    Args:
        image_data: Raw image bytes
        target_format: Target format (JPEG, PNG, WEBP)
        quality: Quality for lossy formats
        
    Returns:
        Converted image bytes
    """
    try:
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary for JPEG
        if target_format.upper() == 'JPEG' and image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
        
        output = io.BytesIO()
        image.save(output, format=target_format.upper(), quality=quality, optimize=True)
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Error converting image format: {e}")
        raise ValueError(f"Failed to convert image format: {e}")


def create_thumbnail(image_data: bytes, size: Tuple[int, int] = (150, 150), 
                    quality: int = 85) -> bytes:
    """
    Create thumbnail from image.
    
    Args:
        image_data: Raw image bytes
        size: Thumbnail size (width, height)
        quality: JPEG quality
        
    Returns:
        Thumbnail image bytes
    """
    try:
        image = Image.open(io.BytesIO(image_data))
        image = _fix_orientation(image)
        
        # Create thumbnail
        image.thumbnail(size, Image.Resampling.LANCZOS)
        
        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
        
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=quality, optimize=True)
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Error creating thumbnail: {e}")
        raise ValueError(f"Failed to create thumbnail: {e}")


def get_image_hash(image_data: bytes) -> str:
    """
    Generate hash for image content.
    
    Args:
        image_data: Raw image bytes
        
    Returns:
        SHA256 hash of image content
    """
    return hashlib.sha256(image_data).hexdigest()


def _fix_orientation(image: Image.Image) -> Image.Image:
    """
    Fix image orientation based on EXIF data.
    
    Args:
        image: PIL Image object
        
    Returns:
        Oriented image
    """
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        
        exif = image.getexif()
        if exif is not None:
            orientation = exif.get(orientation)
            
            if orientation == 3:
                image = image.rotate(180, expand=True)
            elif orientation == 6:
                image = image.rotate(270, expand=True)
            elif orientation == 8:
                image = image.rotate(90, expand=True)
    
    except Exception as e:
        logger.debug(f"No EXIF data or error processing orientation: {e}")
    
    return image


def crop_image(image_data: bytes, box: Tuple[int, int, int, int], 
              quality: int = 85) -> bytes:
    """
    Crop image to specified box.
    
    Args:
        image_data: Raw image bytes
        box: Crop box (left, upper, right, lower)
        quality: JPEG quality
        
    Returns:
        Cropped image bytes
    """
    try:
        image = Image.open(io.BytesIO(image_data))
        cropped = image.crop(box)
        
        if cropped.mode in ('RGBA', 'P'):
            cropped = cropped.convert('RGB')
        
        output = io.BytesIO()
        cropped.save(output, format='JPEG', quality=quality, optimize=True)
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Error cropping image: {e}")
        raise ValueError(f"Failed to crop image: {e}")


def get_best_fit_size(original_width: int, original_height: int, 
                     max_width: int, max_height: int) -> Tuple[int, int]:
    """
    Calculate best fit dimensions for an image.
    
    Args:
        original_width: Original image width
        original_height: Original image height
        max_width: Maximum allowed width
        max_height: Maximum allowed height
        
    Returns:
        Tuple of (width, height) for best fit
    """
    if original_width <= max_width and original_height <= max_height:
        return original_width, original_height
    
    ratio = min(max_width / original_width, max_height / original_height)
    new_width = int(original_width * ratio)
    new_height = int(original_height * ratio)
    
    return new_width, new_height