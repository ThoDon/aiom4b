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


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()
