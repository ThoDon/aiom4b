"""Data models for the AIOM4B application."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Field as SQLField, Relationship


class JobStatus(str, Enum):
    """Job status enumeration."""
    
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobType(str, Enum):
    """Job type enumeration."""
    
    CONVERSION = "conversion"
    TAGGING = "tagging"


# SQLModel database models
class JobDB(SQLModel, table=True):
    """Database model for jobs (conversion and tagging)."""
    
    __tablename__ = "jobs"
    
    id: UUID = SQLField(primary_key=True, default_factory=uuid4)
    job_type: JobType = SQLField(default=JobType.CONVERSION)
    status: JobStatus = SQLField(default=JobStatus.QUEUED)
    input_folders: str = SQLField(description="JSON string of input folders")
    output_file: Optional[str] = SQLField(default=None, description="Path to generated .m4b")
    backup_paths: Optional[str] = SQLField(default=None, description="JSON string of backup paths created during conversion")
    start_time: Optional[datetime] = SQLField(default=None)
    end_time: Optional[datetime] = SQLField(default=None)
    log: Optional[str] = SQLField(default=None, description="Error/info messages")
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)


class TaggedFileDB(SQLModel, table=True):
    """Database model for tagged files."""
    
    __tablename__ = "tagged_files"
    
    id: UUID = SQLField(primary_key=True, default_factory=uuid4)
    file_path: str = SQLField(description="Path to the M4B file")
    asin: Optional[str] = SQLField(default=None, description="Audible ASIN")
    title: Optional[str] = SQLField(default=None, description="Book title")
    author: Optional[str] = SQLField(default=None, description="Author name")
    narrator: Optional[str] = SQLField(default=None, description="Narrator name")
    series: Optional[str] = SQLField(default=None, description="Series name")
    series_part: Optional[str] = SQLField(default=None, description="Series part number")
    description: Optional[str] = SQLField(default=None, description="Book description")
    cover_url: Optional[str] = SQLField(default=None, description="Cover image URL")
    cover_path: Optional[str] = SQLField(default=None, description="Local cover image path")
    is_tagged: bool = SQLField(default=False, description="Whether file has been tagged")
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)


# Pydantic models for API responses
class ConversionJob(BaseModel):
    """Model for conversion job (API response)."""
    
    id: UUID = Field(default_factory=uuid4)
    source_folders: List[str] = Field(..., description="List of source folder paths")
    output_filename: str = Field(..., description="Output M4B filename")
    status: JobStatus = Field(default=JobStatus.QUEUED)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    output_path: Optional[str] = None
    backup_paths: Optional[List[str]] = Field(default=None, description="List of backup paths created during conversion")


class SourceFolder(BaseModel):
    """Model for source folder information."""
    
    path: str = Field(..., description="Folder path")
    mp3_count: int = Field(..., description="Number of MP3 files found")
    total_size_mb: float = Field(..., description="Total size in MB")
    last_modified: datetime = Field(..., description="Last modification time")


class ConversionRequest(BaseModel):
    """Model for conversion request."""
    
    folder_conversions: Dict[str, Optional[str]] = Field(..., description="Dictionary mapping folder paths to output filenames (None for auto-generated)")

class JobResponse(BaseModel):
    """Model for job response."""
    
    job_id: UUID
    status: JobStatus
    message: str


class JobCreate(BaseModel):
    """Model for creating a new job."""
    
    input_folders: List[str] = Field(..., description="List of input folder paths")


class JobUpdate(BaseModel):
    """Model for updating a job."""
    
    status: Optional[JobStatus] = None
    output_file: Optional[str] = None
    backup_paths: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    log: Optional[str] = None


class JobListResponse(BaseModel):
    """Model for job list response."""
    
    jobs: List[ConversionJob]
    total: int
    page: int = 1
    per_page: int = 50


# Tagging models
class TaggedFile(BaseModel):
    """Model for tagged file (API response)."""
    
    id: UUID
    file_path: str
    asin: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    narrator: Optional[str] = None
    series: Optional[str] = None
    series_part: Optional[str] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    cover_path: Optional[str] = None
    is_tagged: bool = False
    created_at: datetime
    updated_at: datetime


class AudibleSearchResult(BaseModel):
    """Model for Audible search results."""
    
    title: str
    author: str
    narrator: Optional[str] = None
    series: Optional[str] = None
    asin: str
    locale: str = "com"


class AudibleBookDetails(BaseModel):
    """Model for detailed Audible book information."""
    
    asin: str
    title: str
    subtitle: Optional[str] = None
    author: str
    authors: List[str] = []
    narrator: Optional[str] = None
    narrators: List[str] = []
    series: Optional[str] = None
    series_part: Optional[str] = None
    description: Optional[str] = None
    publisher_summary: Optional[str] = None
    runtime_length_min: Optional[str] = None
    rating: Optional[str] = None
    release_date: Optional[str] = None
    release_time: Optional[str] = None
    language: Optional[str] = None
    format_type: Optional[str] = None
    publisher_name: Optional[str] = None
    is_adult_product: bool = False
    cover_url: Optional[str] = None
    genres: List[str] = []
    copyright: Optional[str] = None
    isbn: Optional[str] = None
    explicit: bool = False


class TaggingJob(BaseModel):
    """Model for tagging job (API response)."""
    
    id: UUID
    file_path: str
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    metadata: Optional[AudibleBookDetails] = None


class TaggingRequest(BaseModel):
    """Model for tagging request."""
    
    file_path: str
    asin: Optional[str] = None
    search_query: Optional[str] = None


class TaggingJobCreate(BaseModel):
    """Model for creating a tagging job."""
    
    file_path: str
    asin: Optional[str] = None


class TaggingJobUpdate(BaseModel):
    """Model for updating a tagging job."""
    
    status: Optional[JobStatus] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    log: Optional[str] = None
    metadata: Optional[AudibleBookDetails] = None


class TaggedFileListResponse(BaseModel):
    """Model for tagged file list response."""
    
    files: List[TaggedFile]
    total: int
    page: int = 1
    per_page: int = 50


class UnifiedJob(BaseModel):
    """Model for unified job (conversion or tagging) API response."""
    
    id: UUID
    job_type: JobType
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    
    # Conversion job fields
    source_folders: Optional[List[str]] = None
    output_filename: Optional[str] = None
    output_path: Optional[str] = None
    backup_paths: Optional[List[str]] = None
    
    # Tagging job fields
    file_path: Optional[str] = None
    metadata: Optional[AudibleBookDetails] = None


class UnifiedJobListResponse(BaseModel):
    """Model for unified job list response."""
    
    jobs: List[UnifiedJob]
    total: int
    page: int = 1
    per_page: int = 50
