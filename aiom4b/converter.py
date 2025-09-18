"""MP3 to M4B conversion functionality."""

import asyncio
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from uuid import UUID

import ffmpeg

from .config import PROCESSING_DIR, READY_TO_TAG_DIR, USE_ALL_CPUS, BACKUP_ENABLED
from .utils import get_available_cpu_count, create_backup
from .models import ConversionJob, JobStatus, JobUpdate, TaggedFileDB
from .utils import get_mp3_files, sanitize_filename, generate_output_filename_from_folders
from .job_service import job_service
from .database import get_session_sync


class MP3ToM4BConverter:
    """Handles MP3 to M4B conversion using FFmpeg."""
    
    def __init__(self):
        pass
    
    async def convert_folders(
        self,
        job_id: UUID,
        source_folders: List[str],
        output_filename: Optional[str] = None
    ) -> None:
        """Convert MP3 files from multiple folders to a single M4B file with progress tracking."""
        
        try:
            # Generate filename if not provided
            if not output_filename:
                base_filename = generate_output_filename_from_folders(source_folders)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"{base_filename}_{timestamp}.m4b"
            
            output_filename = sanitize_filename(output_filename)
            if not output_filename.endswith(".m4b"):
                output_filename += ".m4b"
            
            # Update job status to running
            job_service.update_job(job_id, JobUpdate(
                status=JobStatus.RUNNING,
                start_time=datetime.utcnow(),
                progress=0.0
            ))
            
            # Create backups if enabled
            backup_paths = []
            if BACKUP_ENABLED:
                for folder in source_folders:
                    backup_path = create_backup(folder)
                    backup_paths.append(backup_path)
            
            # Store backup paths in job
            job_service.update_job(job_id, JobUpdate(
                backup_paths=json.dumps(backup_paths)
            ))
            
            # Collect all MP3 files
            all_mp3_files = []
            for folder in source_folders:
                mp3_files = get_mp3_files(folder)
                all_mp3_files.extend(mp3_files)
            
            if not all_mp3_files:
                raise ValueError("No MP3 files found in the specified folders")
            
            # Sort files by name for consistent ordering
            all_mp3_files.sort(key=lambda x: x.name)
            
            # Create processing output path
            processing_output_path = PROCESSING_DIR / output_filename
            
            # Convert using FFmpeg with progress tracking
            await self._convert_with_ffmpeg_progress(
                all_mp3_files, 
                processing_output_path, 
                job_id
            )
            
            # Move completed file to readyToTag folder
            ready_output_path = READY_TO_TAG_DIR / output_filename
            shutil.move(str(processing_output_path), str(ready_output_path))
            
            # Create database entry for the file
            with get_session_sync() as session:
                tagged_file = TaggedFileDB(
                    file_path=str(ready_output_path),
                    is_tagged=False
                )
                session.add(tagged_file)
                session.commit()
            
            # Update job completion
            job_service.update_job(job_id, JobUpdate(
                status=JobStatus.COMPLETED,
                end_time=datetime.utcnow(),
                progress=100.0,
                output_file=str(ready_output_path)
            ))
            
        except Exception as e:
            # Update job with error
            job_service.update_job(job_id, JobUpdate(
                status=JobStatus.FAILED,
                end_time=datetime.utcnow(),
                log=str(e)
            ))
            
            # Cleanup processing files on failure
            processing_output_path = PROCESSING_DIR / output_filename
            if processing_output_path.exists():
                processing_output_path.unlink()
            
            raise
    
    async def _convert_with_ffmpeg_progress(
        self,
        mp3_files: List[Path],
        output_path: Path,
        job_id: UUID
    ) -> None:
        """Convert MP3 files to M4B using FFmpeg with progress tracking."""
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        total_files = len(mp3_files)
        
        # Create input streams (audio only)
        input_streams = []
        for mp3_file in mp3_files:
            # Select only audio stream (stream 0) to avoid video/album art issues
            input_streams.append(ffmpeg.input(str(mp3_file))['a:0'])
        
        # Configure FFmpeg options
        cpu_count = get_available_cpu_count() if USE_ALL_CPUS else 1
        
        # Create output stream (audio only)
        output_stream = ffmpeg.concat(*input_streams, v=0, a=1)
        
        # Apply audio codec and quality settings
        output_stream = ffmpeg.output(
            output_stream,
            str(output_path),
            acodec='aac',
            **{'b:a': '128k'},  # Audio bitrate
            ac=2,  # Stereo
            ar=44100,  # Sample rate
            threads=cpu_count,
            **{'progress': 'pipe:1'}  # Enable progress reporting to stdout
        )
        
        # Run FFmpeg with progress tracking
        try:
            process = await asyncio.create_subprocess_exec(
                *ffmpeg.compile(output_stream, overwrite_output=True),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Track progress by monitoring FFmpeg output
            progress_task = asyncio.create_task(
                self._track_ffmpeg_progress(process, job_id, total_files)
            )
            
            await process.wait()
            progress_task.cancel()
            
            # Set progress to 100% when conversion actually completes
            job_service.update_job(job_id, JobUpdate(progress=100.0))
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Conversion completed, progress set to 100%")
            
            if process.returncode != 0:
                stderr = await process.stderr.read()
                stdout = await process.stdout.read()
                error_msg = f"FFmpeg conversion failed (return code: {process.returncode})\n"
                error_msg += f"STDERR: {stderr.decode()}\n"
                error_msg += f"STDOUT: {stdout.decode()}"
                raise RuntimeError(error_msg)
                
        except Exception as e:
            raise RuntimeError(f"FFmpeg conversion failed: {e}")
    
    
    async def _track_ffmpeg_progress(
        self,
        process: asyncio.subprocess.Process,
        job_id: UUID,
        total_files: int
    ) -> None:
        """Track FFmpeg progress using smooth time-based estimation."""
        import logging
        
        logger = logging.getLogger(__name__)
        logger.info(f"Starting smooth time-based progress tracking for job {job_id}, total files: {total_files}")
        
        try:
            # Start with 0% progress
            job_service.update_job(job_id, JobUpdate(progress=0.0))
            logger.info(f"Initial progress set to 0%")
            
            # Estimate total time based on file count (roughly 10-15 seconds per file)
            estimated_total_time = total_files * 12.0  # 12 seconds per file average
            start_time = asyncio.get_event_loop().time()
            last_progress = 0.0
            update_count = 0
            
            while process.returncode is None:
                elapsed_time = asyncio.get_event_loop().time() - start_time
                
                # Calculate progress based on elapsed time
                # Use a smooth curve that starts slow and accelerates
                time_progress = min(0.9, elapsed_time / estimated_total_time)  # Cap at 90%
                
                # Apply a smooth curve: slow start, then faster
                if time_progress < 0.1:
                    # Very slow start (0-10% of time = 0-2% progress)
                    progress_percentage = time_progress * 20.0
                elif time_progress < 0.5:
                    # Medium speed (10-50% of time = 2-25% progress)
                    progress_percentage = 2.0 + (time_progress - 0.1) * 57.5
                else:
                    # Faster progress (50-90% of time = 25-90% progress)
                    progress_percentage = 25.0 + (time_progress - 0.5) * 162.5
                
                # Ensure we don't go backwards and update every 2%
                if progress_percentage - last_progress >= 2.0:
                    update_count += 1
                    logger.info(f"Progress update #{update_count}: {progress_percentage:.1f}% (elapsed: {elapsed_time:.1f}s, estimated total: {estimated_total_time:.1f}s)")
                    job_service.update_job(job_id, JobUpdate(progress=progress_percentage))
                    last_progress = progress_percentage
                
                await asyncio.sleep(1.0)  # Update every second
                
        except asyncio.CancelledError:
            logger.info(f"Progress tracking cancelled for job {job_id}")
            pass
        except Exception as e:
            logger.error(f"Progress tracking error: {e}")
            # Don't let progress tracking errors affect the main conversion
            pass
    


# Global converter instance
converter = MP3ToM4BConverter()
