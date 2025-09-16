"""FastAPI routes for the AIOM4B application."""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, status, Query
from fastapi.responses import FileResponse

from .converter import converter
from .models import (
    ConversionJob, ConversionRequest, JobResponse, SourceFolder,
    JobCreate, JobUpdate, JobListResponse, JobStatus
)
from .job_service import job_service
from .utils import get_folder_info, get_mp3_files

router = APIRouter()


@router.get("/folders", response_model=List[SourceFolder])
async def list_source_folders() -> List[SourceFolder]:
    """List all available source folders with MP3 files."""
    from .config import SOURCE_DIR
    
    folders = []
    
    if not SOURCE_DIR.exists():
        return folders
    
    for folder_path in SOURCE_DIR.iterdir():
        if folder_path.is_dir():
            mp3_files = get_mp3_files(str(folder_path))
            if mp3_files:
                mp3_count, total_size_mb, last_modified = get_folder_info(str(folder_path))
                folders.append(SourceFolder(
                    path=str(folder_path),
                    mp3_count=mp3_count,
                    total_size_mb=total_size_mb,
                    last_modified=last_modified
                ))
    
    return folders


@router.post("/convert", response_model=JobResponse)
async def start_conversion(
    request: ConversionRequest,
    background_tasks: BackgroundTasks
) -> JobResponse:
    """Start a new conversion job."""
    
    # Validate source folders
    for folder_path in request.source_folders:
        if not Path(folder_path).exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Source folder does not exist: {folder_path}"
            )
        
        mp3_files = get_mp3_files(folder_path)
        if not mp3_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No MP3 files found in folder: {folder_path}"
            )
    
    # Create job in database
    job_create = JobCreate(input_folders=request.source_folders)
    job_db = job_service.create_job(job_create)
    
    # Start conversion in background
    background_tasks.add_task(
        _run_conversion_task,
        job_db.id,
        request.source_folders,
        request.output_filename
    )
    
    return JobResponse(
        job_id=job_db.id,
        status=job_db.status,
        message=f"Conversion job started with ID: {job_db.id}"
    )




@router.get("/jobs", response_model=List[ConversionJob])
async def list_jobs() -> List[ConversionJob]:
    """List all active conversion jobs (legacy endpoint)."""
    # For backward compatibility, return jobs as array
    jobs_db = job_service.get_jobs(limit=100)
    return [job_service.to_conversion_job(job_db) for job_db in jobs_db]


@router.get("/download/{job_id}")
async def download_file(job_id: UUID) -> FileResponse:
    """Download the converted M4B file."""
    
    job_db = job_service.get_job(job_id)
    if not job_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}"
        )
    
    if job_db.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not completed. Current status: {job_db.status}"
        )
    
    if not job_db.output_file or not Path(job_db.output_file).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output file not found"
        )
    
    # Extract filename from output_file path
    output_filename = Path(job_db.output_file).name
    
    return FileResponse(
        path=job_db.output_file,
        filename=output_filename,
        media_type="audio/mp4"
    )


# Job management endpoints
@router.get("/jobs/paginated", response_model=JobListResponse)
async def list_jobs_paginated(
    status_filter: Optional[JobStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100)
) -> JobListResponse:
    """List all jobs with optional filtering and pagination."""
    
    offset = (page - 1) * per_page
    jobs_db = job_service.get_jobs(status=status_filter, limit=per_page, offset=offset)
    
    # Convert to API models
    jobs = [job_service.to_conversion_job(job_db) for job_db in jobs_db]
    
    # Get total count (simplified - in production you'd want a separate count query)
    total_jobs = job_service.get_jobs(status=status_filter, limit=1000, offset=0)
    total = len(total_jobs)
    
    return JobListResponse(
        jobs=jobs,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/jobs/{job_id}", response_model=ConversionJob)
async def get_job_details(job_id: UUID) -> ConversionJob:
    """Get detailed information about a specific job."""
    
    job_db = job_service.get_job(job_id)
    if not job_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}"
        )
    
    return job_service.to_conversion_job(job_db)


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: UUID) -> dict:
    """Delete a job record."""
    
    success = job_service.delete_job(job_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}"
        )
    
    return {"message": f"Job {job_id} deleted successfully"}


@router.post("/jobs/clear")
async def clear_old_jobs(days_old: int = Query(30, ge=1, le=365)) -> dict:
    """Clear old completed/failed jobs."""
    
    deleted_count = job_service.clear_old_jobs(days_old)
    return {"message": f"Cleared {deleted_count} old jobs"}


async def _run_conversion_task(
    job_id: UUID,
    source_folders: List[str],
    output_filename: Optional[str] = None
) -> None:
    """Background task to run the actual conversion and update the database."""
    
    try:
        # Update job status to running
        job_service.update_job(job_id, JobUpdate(
            status=JobStatus.RUNNING,
            start_time=datetime.utcnow()
        ))
        
        # Run the actual conversion
        job = await converter.convert_folders(
            source_folders=source_folders,
            output_filename=output_filename,
            job_id=str(job_id)
        )
        
        # Update job with results
        job_service.update_job(job_id, JobUpdate(
            status=JobStatus.COMPLETED,
            end_time=datetime.utcnow(),
            output_file=job.output_path
        ))
        
    except Exception as e:
        # Update job with error
        job_service.update_job(job_id, JobUpdate(
            status=JobStatus.FAILED,
            end_time=datetime.utcnow(),
            log=str(e)
        ))
