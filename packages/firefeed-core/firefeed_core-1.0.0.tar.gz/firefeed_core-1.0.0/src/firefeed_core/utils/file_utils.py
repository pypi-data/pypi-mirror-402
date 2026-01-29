"""
File Utilities

Common file utilities for FireFeed microservices.
"""

import os
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Union, BinaryIO, TextIO, List
import hashlib

logger = logging.getLogger(__name__)


def safe_file_path(file_path: Union[str, Path], 
                  allowed_directories: Optional[List[str]] = None) -> bool:
    """
    Check if file path is safe (prevents directory traversal attacks).
    
    Args:
        file_path: File path to check
        allowed_directories: List of allowed directories
        
    Returns:
        True if path is safe, False otherwise
    """
    try:
        path = Path(file_path).resolve()
        
        # Check for directory traversal
        if '..' in str(path) or path.is_absolute() and not any(
            str(path).startswith(os.path.abspath(d)) for d in (allowed_directories or [])
        ):
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking file path safety: {e}")
        return False


def get_file_extension(file_path: Union[str, Path]) -> str:
    """
    Get file extension.
    
    Args:
        file_path: File path
        
    Returns:
        File extension (lowercase, without dot)
    """
    try:
        return Path(file_path).suffix.lower().lstrip('.')
    except Exception as e:
        logger.error(f"Error getting file extension: {e}")
        return ""


def create_directory(directory_path: Union[str, Path], 
                    mode: int = 0o755) -> bool:
    """
    Create directory if it doesn't exist.
    
    Args:
        directory_path: Directory path
        mode: Directory permissions
        
    Returns:
        True if directory was created or already exists, False otherwise
    """
    try:
        Path(directory_path).mkdir(parents=True, exist_ok=True)
        os.chmod(directory_path, mode)
        return True
    except Exception as e:
        logger.error(f"Error creating directory: {e}")
        return False


def delete_file(file_path: Union[str, Path]) -> bool:
    """
    Delete file safely.
    
    Args:
        file_path: File path
        
    Returns:
        True if file was deleted or doesn't exist, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return True  # File doesn't exist, consider success
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        return False


def copy_file(source_path: Union[str, Path], 
             destination_path: Union[str, Path]) -> bool:
    """
    Copy file.
    
    Args:
        source_path: Source file path
        destination_path: Destination file path
        
    Returns:
        True if file was copied successfully, False otherwise
    """
    try:
        shutil.copy2(source_path, destination_path)
        return True
    except Exception as e:
        logger.error(f"Error copying file: {e}")
        return False


def move_file(source_path: Union[str, Path], 
             destination_path: Union[str, Path]) -> bool:
    """
    Move file.
    
    Args:
        source_path: Source file path
        destination_path: Destination file path
        
    Returns:
        True if file was moved successfully, False otherwise
    """
    try:
        shutil.move(source_path, destination_path)
        return True
    except Exception as e:
        logger.error(f"Error moving file: {e}")
        return False


def get_file_size(file_path: Union[str, Path]) -> int:
    """
    Get file size in bytes.
    
    Args:
        file_path: File path
        
    Returns:
        File size in bytes, 0 if file doesn't exist
    """
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        logger.error(f"Error getting file size: {e}")
        return 0


def get_file_hash(file_path: Union[str, Path], 
                 algorithm: str = 'sha256') -> Optional[str]:
    """
    Calculate file hash.
    
    Args:
        file_path: File path
        algorithm: Hash algorithm ('md5', 'sha1', 'sha256')
        
    Returns:
        File hash as hex string, None if error
    """
    try:
        hash_func = getattr(hashlib, algorithm.lower(), None)
        if not hash_func:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")
        
        hash_obj = hash_func()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
        
    except Exception as e:
        logger.error(f"Error calculating file hash: {e}")
        return None


def is_file_readable(file_path: Union[str, Path]) -> bool:
    """
    Check if file is readable.
    
    Args:
        file_path: File path
        
    Returns:
        True if file is readable, False otherwise
    """
    try:
        return os.path.isfile(file_path) and os.access(file_path, os.R_OK)
    except Exception as e:
        logger.error(f"Error checking file readability: {e}")
        return False


def is_file_writable(file_path: Union[str, Path]) -> bool:
    """
    Check if file is writable.
    
    Args:
        file_path: File path
        
    Returns:
        True if file is writable, False otherwise
    """
    try:
        if os.path.exists(file_path):
            return os.access(file_path, os.W_OK)
        else:
            # Check if directory is writable
            return os.access(os.path.dirname(file_path), os.W_OK)
    except Exception as e:
        logger.error(f"Error checking file writability: {e}")
        return False


def create_temp_file(suffix: str = '', prefix: str = 'temp_',
                    directory: Optional[str] = None) -> str:
    """
    Create temporary file.
    
    Args:
        suffix: File suffix
        prefix: File prefix
        directory: Directory for temp file
        
    Returns:
        Path to temporary file
    """
    try:
        fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=directory)
        os.close(fd)  # Close the file descriptor
        return path
    except Exception as e:
        logger.error(f"Error creating temporary file: {e}")
        raise


def create_temp_directory(prefix: str = 'temp_',
                         directory: Optional[str] = None) -> str:
    """
    Create temporary directory.
    
    Args:
        prefix: Directory prefix
        directory: Parent directory
        
    Returns:
        Path to temporary directory
    """
    try:
        return tempfile.mkdtemp(prefix=prefix, dir=directory)
    except Exception as e:
        logger.error(f"Error creating temporary directory: {e}")
        raise


def get_file_mime_type(file_path: Union[str, Path]) -> Optional[str]:
    """
    Get file MIME type.
    
    Args:
        file_path: File path
        
    Returns:
        MIME type string, None if error
    """
    try:
        import mimetypes
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type
    except Exception as e:
        logger.error(f"Error getting file MIME type: {e}")
        return None


def validate_file_type(file_path: Union[str, Path], 
                      allowed_extensions: Optional[List[str]] = None,
                      allowed_mime_types: Optional[List[str]] = None) -> bool:
    """
    Validate file type by extension and MIME type.
    
    Args:
        file_path: File path
        allowed_extensions: List of allowed file extensions
        allowed_mime_types: List of allowed MIME types
        
    Returns:
        True if file type is valid, False otherwise
    """
    try:
        # Check extension
        if allowed_extensions:
            extension = get_file_extension(file_path)
            if extension not in [ext.lower().lstrip('.') for ext in allowed_extensions]:
                return False
        
        # Check MIME type
        if allowed_mime_types:
            mime_type = get_file_mime_type(file_path)
            if mime_type not in allowed_mime_types:
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating file type: {e}")
        return False


def read_file_chunked(file_path: Union[str, Path], 
                     chunk_size: int = 8192) -> bytes:
    """
    Read file in chunks.
    
    Args:
        file_path: File path
        chunk_size: Chunk size in bytes
        
    Yields:
        File chunks as bytes
    """
    try:
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk
    except Exception as e:
        logger.error(f"Error reading file in chunks: {e}")
        raise


def write_file_chunked(file_path: Union[str, Path], 
                      chunks: list, 
                      mode: str = 'wb') -> bool:
    """
    Write file from chunks.
    
    Args:
        file_path: File path
        chunks: List of file chunks
        mode: File mode
        
    Returns:
        True if file was written successfully, False otherwise
    """
    try:
        with open(file_path, mode) as f:
            for chunk in chunks:
                f.write(chunk)
        return True
    except Exception as e:
        logger.error(f"Error writing file from chunks: {e}")
        return False


def get_directory_size(directory_path: Union[str, Path]) -> int:
    """
    Get total size of directory.
    
    Args:
        directory_path: Directory path
        
    Returns:
        Total size in bytes
    """
    try:
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
        return total_size
    except Exception as e:
        logger.error(f"Error getting directory size: {e}")
        return 0


def cleanup_directory(directory_path: Union[str, Path], 
                     max_age_hours: int = 24) -> bool:
    """
    Clean up old files in directory.
    
    Args:
        directory_path: Directory path
        max_age_hours: Maximum age of files in hours
        
    Returns:
        True if cleanup was successful, False otherwise
    """
    try:
        import time
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for filename in os.listdir(directory_path):
            filepath = os.path.join(directory_path, filename)
            if os.path.isfile(filepath):
                file_age = current_time - os.path.getmtime(filepath)
                if file_age > max_age_seconds:
                    os.remove(filepath)
        
        return True
    except Exception as e:
        logger.error(f"Error cleaning up directory: {e}")
        return False