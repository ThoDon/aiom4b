"""Utility functions for the AIOM4B application."""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from .config import BACKUP_DIR, SUPPORTED_AUDIO_FORMATS


def get_mp3_files(folder_path: str) -> List[Path]:
    """Recursively find all MP3 files in a folder."""
    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        return []
    
    mp3_files = []
    for file_path in folder.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_AUDIO_FORMATS:
            mp3_files.append(file_path)
    
    return sorted(mp3_files)


def get_folder_info(folder_path: str) -> Tuple[int, float, datetime]:
    """Get information about a folder (MP3 count, total size, last modified)."""
    mp3_files = get_mp3_files(folder_path)
    
    if not mp3_files:
        return 0, 0.0, datetime.fromtimestamp(0)
    
    total_size = sum(file.stat().st_size for file in mp3_files)
    total_size_mb = total_size / (1024 * 1024)
    
    last_modified = max(file.stat().st_mtime for file in mp3_files)
    last_modified_dt = datetime.fromtimestamp(last_modified)
    
    return len(mp3_files), total_size_mb, last_modified_dt


def create_backup(folder_path: str) -> str:
    """Create a timestamped backup of a folder."""
    if not BACKUP_DIR.exists():
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = Path(folder_path).name
    backup_name = f"{folder_name}_{timestamp}"
    backup_path = BACKUP_DIR / backup_name
    
    shutil.copytree(folder_path, backup_path)
    return str(backup_path)


def get_available_cpu_count() -> int:
    """Get the number of available CPU cores."""
    return os.cpu_count() or 1


def cleanup_backup_files(backup_paths: List[str]) -> None:
    """Clean up backup files after successful tagging."""
    for backup_path in backup_paths:
        try:
            if Path(backup_path).exists():
                shutil.rmtree(backup_path)
                print(f"Cleaned up backup: {backup_path}")
        except Exception as e:
            print(f"Failed to clean up backup {backup_path}: {e}")


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters and cleaning up the name."""
    import re
    
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove or replace other problematic characters
    filename = re.sub(r'[^\w\s\-_\.]', '_', filename)
    
    # Clean up multiple underscores and spaces
    filename = re.sub(r'[_\s]+', '_', filename)
    
    # Remove leading/trailing underscores and spaces
    filename = filename.strip('_ ')
    
    # Ensure it's not empty
    if not filename:
        filename = "converted"
    
    return filename


def generate_output_filename_from_folders(source_folders: List[str]) -> str:
    """Generate a clean output filename from source folder names."""
    if not source_folders:
        return "converted"
    
    # If only one folder, use its name
    if len(source_folders) == 1:
        folder_path = Path(source_folders[0])
        folder_name = folder_path.name
        
        # Handle edge cases where the path doesn't have a meaningful name
        # Check if the path ends with just the name (indicating it's a meaningful folder)
        if (not folder_name or 
            folder_name in ['/', '\\'] or 
            not source_folders[0].endswith(folder_name) or
            len(folder_name) < 2):  # Very short names might not be meaningful
            return "converted"
            
        sanitized = sanitize_filename(folder_name)
        return sanitized if sanitized != "converted" else "converted"
    
    # For multiple folders, create a combined name
    folder_names = []
    for folder in source_folders:
        folder_name = Path(folder).name
        sanitized = sanitize_filename(folder_name)
        if sanitized != "converted":  # Only include valid folder names
            folder_names.append(sanitized)
    
    if not folder_names:
        return "converted"
    
    combined_name = "_and_".join(folder_names)
    return sanitize_filename(combined_name)
