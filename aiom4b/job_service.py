"""Job service for managing conversion jobs in the database."""

import json
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlmodel import Session, select, and_, or_

from .database import get_session_sync
from .models import JobDB, JobStatus, JobType, ConversionJob, JobCreate, JobUpdate, TaggingJob, TaggingJobCreate, TaggingJobUpdate, UnifiedJob


class JobService:
    """Service for managing conversion jobs."""
    
    def __init__(self):
        self.session = get_session_sync()
    
    def create_job(self, job_data: JobCreate) -> JobDB:
        """Create a new conversion job in the database."""
        job = JobDB(
            job_type=JobType.CONVERSION,
            input_folders=json.dumps(job_data.input_folders),
            status=JobStatus.QUEUED
        )
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job
    
    def create_tagging_job(self, job_data: TaggingJobCreate) -> JobDB:
        """Create a new tagging job in the database."""
        job = JobDB(
            job_type=JobType.TAGGING,
            input_folders=json.dumps([job_data.file_path]),
            status=JobStatus.QUEUED
        )
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job
    
    def get_job(self, job_id: UUID) -> Optional[JobDB]:
        """Get a job by ID."""
        statement = select(JobDB).where(JobDB.id == job_id)
        return self.session.exec(statement).first()
    
    def get_jobs(
        self, 
        status: Optional[JobStatus] = None,
        job_type: Optional[JobType] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[JobDB]:
        """Get jobs with optional filtering."""
        statement = select(JobDB)
        
        if status:
            statement = statement.where(JobDB.status == status)
        
        if job_type:
            statement = statement.where(JobDB.job_type == job_type)
        
        statement = statement.order_by(JobDB.created_at.desc()).offset(offset).limit(limit)
        return list(self.session.exec(statement))
    
    def update_job(self, job_id: UUID, job_update: JobUpdate) -> Optional[JobDB]:
        """Update a job."""
        job = self.get_job(job_id)
        if not job:
            return None
        
        # Update fields if provided
        if job_update.status is not None:
            job.status = job_update.status
        if job_update.output_file is not None:
            job.output_file = job_update.output_file
        if job_update.backup_paths is not None:
            job.backup_paths = job_update.backup_paths
        if job_update.progress is not None:
            job.progress = job_update.progress
        if job_update.start_time is not None:
            job.start_time = job_update.start_time
        if job_update.end_time is not None:
            job.end_time = job_update.end_time
        if job_update.log is not None:
            job.log = job_update.log
        
        job.updated_at = datetime.utcnow()
        
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job
    
    def delete_job(self, job_id: UUID) -> bool:
        """Delete a job."""
        job = self.get_job(job_id)
        if not job:
            return False
        
        self.session.delete(job)
        self.session.commit()
        return True
    
    def clear_old_jobs(self, days_old: int = 30) -> int:
        """Clear old completed/failed jobs."""
        cutoff_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date - timedelta(days=days_old)
        
        statement = select(JobDB).where(
            and_(
                or_(JobDB.status == JobStatus.COMPLETED, JobDB.status == JobStatus.FAILED),
                JobDB.created_at < cutoff_date
            )
        )
        
        old_jobs = list(self.session.exec(statement))
        for job in old_jobs:
            self.session.delete(job)
        
        self.session.commit()
        return len(old_jobs)
    
    def count_jobs(
        self, 
        status: Optional[JobStatus] = None,
        job_type: Optional[JobType] = None
    ) -> int:
        """Count jobs with optional filtering."""
        conditions = []
        
        if status:
            conditions.append(JobDB.status == status)
        
        if job_type:
            conditions.append(JobDB.job_type == job_type)
        
        statement = select(JobDB)
        if conditions:
            statement = statement.where(and_(*conditions))
        
        jobs = self.session.exec(statement).all()
        return len(jobs)
    
    def to_conversion_job(self, job_db: JobDB) -> ConversionJob:
        """Convert JobDB to ConversionJob for API responses."""
        input_folders = json.loads(job_db.input_folders) if job_db.input_folders else []
        backup_paths = json.loads(job_db.backup_paths) if job_db.backup_paths else []
        
        # Extract filename from output_file path
        output_filename = ""
        if job_db.output_file:
            from pathlib import Path
            output_filename = Path(job_db.output_file).name
        
        return ConversionJob(
            id=job_db.id,
            source_folders=input_folders,
            output_filename=output_filename,
            status=job_db.status,
            created_at=job_db.created_at,
            started_at=job_db.start_time,
            completed_at=job_db.end_time,
            error_message=job_db.log if job_db.status == JobStatus.FAILED else None,
            progress=job_db.progress,
            output_path=job_db.output_file,
            backup_paths=backup_paths
        )
    
    def to_tagging_job(self, job_db: JobDB) -> TaggingJob:
        """Convert JobDB to TaggingJob for API responses."""
        input_folders = json.loads(job_db.input_folders) if job_db.input_folders else []
        file_path = input_folders[0] if input_folders else ""
        
        return TaggingJob(
            id=job_db.id,
            file_path=file_path,
            status=job_db.status,
            created_at=job_db.created_at,
            started_at=job_db.start_time,
            completed_at=job_db.end_time,
            error_message=job_db.log if job_db.status == JobStatus.FAILED else None,
            progress=job_db.progress,
            metadata=None  # TODO: Load metadata from tagged file if available
        )
    
    def to_unified_job(self, job_db: JobDB) -> UnifiedJob:
        """Convert JobDB to UnifiedJob for API responses."""
        input_folders = json.loads(job_db.input_folders) if job_db.input_folders else []
        backup_paths = json.loads(job_db.backup_paths) if job_db.backup_paths else []
        
        # Extract filename from output_file path
        output_filename = ""
        if job_db.output_file:
            from pathlib import Path
            output_filename = Path(job_db.output_file).name
        
        # Use actual progress from database
        progress = job_db.progress
        
        # Create unified job with appropriate fields based on job type
        if job_db.job_type == JobType.CONVERSION:
            return UnifiedJob(
                id=job_db.id,
                job_type=job_db.job_type,
                status=job_db.status,
                created_at=job_db.created_at,
                started_at=job_db.start_time,
                completed_at=job_db.end_time,
                error_message=job_db.log if job_db.status == JobStatus.FAILED else None,
                progress=progress,
                source_folders=input_folders,
                output_filename=output_filename,
                output_path=job_db.output_file,
                backup_paths=backup_paths,
                file_path=None,
                metadata=None
            )
        else:  # TAGGING
            file_path = input_folders[0] if input_folders else ""
            return UnifiedJob(
                id=job_db.id,
                job_type=job_db.job_type,
                status=job_db.status,
                created_at=job_db.created_at,
                started_at=job_db.start_time,
                completed_at=job_db.end_time,
                error_message=job_db.log if job_db.status == JobStatus.FAILED else None,
                progress=progress,
                source_folders=None,
                output_filename=None,
                output_path=None,
                backup_paths=None,
                file_path=file_path,
                metadata=None  # TODO: Load metadata from tagged file if available
            )


# Global job service instance
job_service = JobService()
