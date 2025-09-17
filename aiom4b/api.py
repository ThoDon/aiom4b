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
    JobCreate, JobUpdate, JobListResponse, JobStatus, JobType,
    TaggedFile, TaggedFileListResponse, AudibleSearchResult, AudibleBookDetails,
    TaggingJob, TaggingJobCreate, TaggingJobUpdate, TaggingRequest,
    UnifiedJob, UnifiedJobListResponse
)
from .job_service import job_service
from .tagging_service import tagging_service
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


@router.post("/convert", response_model=List[JobResponse])
async def start_conversion(
    request: ConversionRequest,
    background_tasks: BackgroundTasks
) -> List[JobResponse]:
    """Start conversion jobs (one per folder). Each folder is treated as a separate unit."""
    
    job_responses = []
    
    for folder_path, output_filename in request.folder_conversions.items():
        # Validate source folder
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
        
        # Create job in database (one per folder)
        job_create = JobCreate(input_folders=[folder_path])
        job_db = job_service.create_job(job_create)
        
        # Start conversion in background (one per folder)
        background_tasks.add_task(
            _run_conversion_task,
            job_db.id,
            [folder_path],
            output_filename
        )
        
        job_responses.append(JobResponse(
            job_id=job_db.id,
            status=job_db.status,
            message=f"Conversion job started with ID: {job_db.id}"
        ))
    
    return job_responses






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
    job_type_filter: Optional[JobType] = Query(None, alias="type"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100)
) -> JobListResponse:
    """List all jobs with optional filtering and pagination."""
    
    offset = (page - 1) * per_page
    jobs_db = job_service.get_jobs(
        status=status_filter, 
        job_type=job_type_filter,
        limit=per_page, 
        offset=offset
    )
    
    # Convert to API models (only conversion jobs for now)
    jobs = [job_service.to_conversion_job(job_db) for job_db in jobs_db if job_db.job_type == JobType.CONVERSION]
    
    # Get total count (simplified - in production you'd want a separate count query)
    total_jobs = job_service.get_jobs(
        status=status_filter, 
        job_type=job_type_filter,
        limit=1000, 
        offset=0
    )
    total = len([j for j in total_jobs if j.job_type == JobType.CONVERSION])
    
    return JobListResponse(
        jobs=jobs,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/jobs/tagging", response_model=List[TaggingJob])
async def list_tagging_jobs() -> List[TaggingJob]:
    """List all tagging jobs."""
    
    jobs_db = job_service.get_jobs(job_type=JobType.TAGGING, limit=100)
    return [job_service.to_tagging_job(job_db) for job_db in jobs_db]


@router.get("/jobs/unified", response_model=UnifiedJobListResponse)
async def list_unified_jobs(
    status_filter: Optional[JobStatus] = Query(None, alias="status"),
    job_type_filter: Optional[JobType] = Query(None, alias="type"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100)
) -> UnifiedJobListResponse:
    """List all jobs (conversion and tagging) with optional filtering and pagination."""
    
    offset = (page - 1) * per_page
    
    # Get jobs with filters
    jobs_db = job_service.get_jobs(
        status=status_filter,
        job_type=job_type_filter,
        limit=per_page,
        offset=offset
    )
    
    # Get total count for pagination
    total_count = job_service.count_jobs(
        status=status_filter,
        job_type=job_type_filter
    )
    
    # Convert to unified jobs
    unified_jobs = [job_service.to_unified_job(job_db) for job_db in jobs_db]
    
    return UnifiedJobListResponse(
        jobs=unified_jobs,
        total=total_count,
        page=page,
        per_page=per_page
    )


@router.get("/jobs/tagging/{job_id}", response_model=TaggingJob)
async def get_tagging_job_details(job_id: UUID) -> TaggingJob:
    """Get detailed information about a specific tagging job."""
    
    job_db = job_service.get_job(job_id)
    if not job_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}"
        )
    
    if job_db.job_type != JobType.TAGGING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job {job_id} is not a tagging job"
        )
    
    return job_service.to_tagging_job(job_db)


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
        backup_paths_json = json.dumps(job.backup_paths) if job.backup_paths else None
        job_service.update_job(job_id, JobUpdate(
            status=JobStatus.COMPLETED,
            end_time=datetime.utcnow(),
            output_file=job.output_path,
            backup_paths=backup_paths_json
        ))
        
    except Exception as e:
        # Update job with error
        job_service.update_job(job_id, JobUpdate(
            status=JobStatus.FAILED,
            end_time=datetime.utcnow(),
            log=str(e)
        ))


# Tagging endpoints
@router.get("/files/untagged", response_model=TaggedFileListResponse)
async def list_untagged_files(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100)
) -> TaggedFileListResponse:
    """List all converted but untagged M4B files."""
    
    offset = (page - 1) * per_page
    files = tagging_service.get_untagged_files(limit=per_page, offset=offset)
    
    # Get total count (simplified - in production you'd want a separate count query)
    total_files = tagging_service.get_untagged_files(limit=1000, offset=0)
    total = len(total_files)
    
    return TaggedFileListResponse(
        files=files,
        total=total,
        page=page,
        per_page=per_page
    )


@router.post("/jobs/tagging", response_model=JobResponse)
async def create_tagging_job(
    request: TaggingJobCreate,
    background_tasks: BackgroundTasks
) -> JobResponse:
    """Create a tagging job for a file."""
    
    # Validate file exists
    if not Path(request.file_path).exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File does not exist: {request.file_path}"
        )
    
    # Create job in database
    job_db = job_service.create_tagging_job(request)
    
    # Start tagging in background
    background_tasks.add_task(
        _run_tagging_task,
        job_db.id,
        request.file_path,
        request.asin
    )
    
    return JobResponse(
        job_id=job_db.id,
        status=job_db.status,
        message=f"Tagging job started with ID: {job_db.id}"
    )


@router.post("/files/{file_id}/search", response_model=List[AudibleSearchResult])
async def search_audible_metadata(
    file_id: UUID,
    query: str = Query(..., description="Search query for Audible API")
) -> List[AudibleSearchResult]:
    """Search Audible API for metadata using a query."""
    
    # Verify file exists
    tagged_file = tagging_service.get_tagged_file(file_id)
    if not tagged_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {file_id}"
        )
    
    # Search Audible
    results = tagging_service.search_audible(query)
    return results


@router.post("/files/{file_id}/apply")
async def apply_metadata_to_file(
    file_id: UUID,
    asin: str = Query(..., description="ASIN of the book to apply")
) -> dict:
    """Apply selected metadata to a file."""
    
    # Validate file exists first
    tagged_file = tagging_service.get_tagged_file(file_id)
    if not tagged_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID {file_id} not found"
        )
    
    # Get book details from Audible
    book_details = tagging_service.get_book_details(asin)
    if not book_details:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not find book details for ASIN: {asin}. The ASIN may be invalid, the book may not be available on Audible, or it may be from a different region."
        )
    
    # Apply metadata to file
    success = tagging_service.apply_metadata_to_file(file_id, book_details)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply metadata to file. Check server logs for details."
        )
    
    return {"message": "Metadata applied successfully"}


@router.delete("/files/{file_id}")
async def delete_tagged_file(file_id: UUID) -> dict:
    """Delete a tagged file record."""
    
    success = tagging_service.delete_tagged_file(file_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {file_id}"
        )
    
    return {"message": f"File {file_id} deleted successfully"}


async def _run_tagging_task(
    job_id: UUID,
    file_path: str,
    asin: Optional[str] = None
) -> None:
    """Background task to run the actual tagging and update the database."""
    
    try:
        # Update job status to running
        job_service.update_job(job_id, JobUpdate(
            status=JobStatus.RUNNING,
            start_time=datetime.utcnow()
        ))
        
        # If ASIN is provided, get book details directly
        if asin:
            book_details = tagging_service.get_book_details(asin)
            if not book_details:
                raise Exception(f"Could not fetch book details for ASIN: {asin}")
        else:
            # TODO: Implement automatic search based on filename
            # For now, we'll just mark the job as completed without metadata
            book_details = None
        
        # Apply metadata if available
        if book_details:
            # Find the tagged file record
            tagged_file = tagging_service.get_tagged_file_by_path(file_path)
            if tagged_file:
                tagging_service.apply_metadata_to_file(tagged_file.id, book_details)
        
        # Update job with results
        job_service.update_job(job_id, JobUpdate(
            status=JobStatus.COMPLETED,
            end_time=datetime.utcnow()
        ))
        
    except Exception as e:
        # Update job with error
        job_service.update_job(job_id, JobUpdate(
            status=JobStatus.FAILED,
            end_time=datetime.utcnow(),
            log=str(e)
        ))
