"""MP3 to M4B conversion functionality."""

import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import ffmpeg

from .config import OUTPUT_DIR, USE_ALL_CPUS, BACKUP_ENABLED
from .utils import get_available_cpu_count, create_backup
from .models import ConversionJob, JobStatus
from .utils import get_mp3_files, sanitize_filename, generate_output_filename_from_folders


class MP3ToM4BConverter:
    """Handles MP3 to M4B conversion using FFmpeg."""
    
    def __init__(self):
        pass
    
    async def convert_folders(
        self,
        source_folders: List[str],
        output_filename: Optional[str] = None,
        job_id: Optional[str] = None
    ) -> ConversionJob:
        """Convert MP3 files from multiple folders to a single M4B file."""
        
        # Create job
        if not output_filename:
            # Generate filename from folder names for cleaner output
            base_filename = generate_output_filename_from_folders(source_folders)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{base_filename}_{timestamp}.m4b"
        
        output_filename = sanitize_filename(output_filename)
        if not output_filename.endswith(".m4b"):
            output_filename += ".m4b"
        
        job = ConversionJob(
            source_folders=source_folders,
            output_filename=output_filename
        )
        
        if job_id:
            job.id = job_id
        
        # Job is now managed by the database, no need to store in memory
        
        try:
            # Update job status
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            
            # Create backups if enabled
            backup_paths = []
            if BACKUP_ENABLED:
                for folder in source_folders:
                    backup_path = create_backup(folder)
                    backup_paths.append(backup_path)
            
            # Store backup paths in job for later cleanup
            job.backup_paths = backup_paths
            
            # Collect all MP3 files
            all_mp3_files = []
            for folder in source_folders:
                mp3_files = get_mp3_files(folder)
                all_mp3_files.extend(mp3_files)
            
            if not all_mp3_files:
                raise ValueError("No MP3 files found in the specified folders")
            
            # Sort files by name for consistent ordering
            all_mp3_files.sort(key=lambda x: x.name)
            
            # Create output path
            output_path = OUTPUT_DIR / output_filename
            
            # Convert using FFmpeg
            await self._convert_with_ffmpeg(all_mp3_files, output_path, job)
            
            # Update job completion
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.progress = 100.0
            job.output_path = str(output_path)
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error_message = str(e)
            raise
        
        finally:
            # Job cleanup is now handled by the database
            pass
        
        return job
    
    async def _convert_with_ffmpeg(
        self,
        mp3_files: List[Path],
        output_path: Path,
        job: ConversionJob
    ) -> None:
        """Convert MP3 files to M4B using FFmpeg."""
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create input streams
        input_streams = []
        for mp3_file in mp3_files:
            input_streams.append(ffmpeg.input(str(mp3_file)))
        
        # Configure FFmpeg options
        cpu_count = get_available_cpu_count() if USE_ALL_CPUS else 1
        
        # Create output stream
        output_stream = ffmpeg.concat(*input_streams, v=0, a=1)
        
        # Apply audio codec and quality settings
        output_stream = ffmpeg.output(
            output_stream,
            str(output_path),
            acodec='aac',
            audio_bitrate='128k',
            ac=2,  # Stereo
            ar=44100,  # Sample rate
            threads=cpu_count
        )
        
        # Run FFmpeg
        try:
            process = await asyncio.create_subprocess_exec(
                *ffmpeg.compile(output_stream, overwrite_output=True),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.wait()
            
            if process.returncode != 0:
                stderr = await process.stderr.read()
                stdout = await process.stdout.read()
                error_msg = f"FFmpeg conversion failed (return code: {process.returncode})\n"
                error_msg += f"STDERR: {stderr.decode()}\n"
                error_msg += f"STDOUT: {stdout.decode()}"
                raise RuntimeError(error_msg)
                
        except Exception as e:
            raise RuntimeError(f"FFmpeg conversion failed: {e}")
    


# Global converter instance
converter = MP3ToM4BConverter()
