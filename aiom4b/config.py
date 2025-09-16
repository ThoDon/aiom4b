"""Configuration settings for the AIOM4B application."""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
SOURCE_DIR = BASE_DIR / "source"
OUTPUT_DIR = DATA_DIR / "output"
BACKUP_DIR = DATA_DIR / "backup"

# Create directories if they don't exist
for directory in [DATA_DIR, SOURCE_DIR, OUTPUT_DIR, BACKUP_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Application settings
APP_NAME = "AIOM4B"
APP_VERSION = "0.1.0"
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# API settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Processing settings
MAX_CONCURRENT_JOBS = int(os.getenv("MAX_CONCURRENT_JOBS", "4"))
USE_ALL_CPUS = os.getenv("USE_ALL_CPUS", "true").lower() == "true"

# File settings
SUPPORTED_AUDIO_FORMATS = [".mp3"]
OUTPUT_FORMAT = ".m4b"
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "1000"))

# Backup settings
BACKUP_ENABLED = os.getenv("BACKUP_ENABLED", "true").lower() == "true"
BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
