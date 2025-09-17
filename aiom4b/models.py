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


# SQLModel database models
class JobDB(SQLModel, table=True):
    """Database model for conversion jobs."""
    
    __tablename__ = "jobs"
    
    id: UUID = SQLField(primary_key=True, default_factory=uuid4)
    status: JobStatus = SQLField(default=JobStatus.QUEUED)
    input_folders: str = SQLField(description="JSON string of input folders")
    output_file: Optional[str] = SQLField(default=None, description="Path to generated .m4b")
    start_time: Optional[datetime] = SQLField(default=None)
    end_time: Optional[datetime] = SQLField(default=None)
    log: Optional[str] = SQLField(default=None, description="Error/info messages")
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
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    log: Optional[str] = None


class JobListResponse(BaseModel):
    """Model for job list response."""
    
    jobs: List[ConversionJob]
    total: int
    page: int = 1
    per_page: int = 50
