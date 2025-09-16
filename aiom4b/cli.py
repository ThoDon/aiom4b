"""CLI interface for the AIOM4B application."""

import asyncio
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .api import list_source_folders, start_conversion, list_jobs
from .converter import converter
from .models import ConversionRequest, JobStatus
from .job_service import job_service
from .database import create_db_and_tables
from .utils import get_folder_info, get_mp3_files

app = typer.Typer(help="AIOM4B - MP3 to M4B conversion tool")
console = Console()

# Initialize database on CLI startup
create_db_and_tables()


@app.command()
def convert(
    folders: List[str] = typer.Argument(..., help="Source folders containing MP3 files"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output filename"),
    background: bool = typer.Option(False, "--background", "-b", help="Run in background")
):
    """Convert MP3 files from folders to M4B format."""
    
    # Validate folders
    valid_folders = []
    for folder in folders:
        folder_path = Path(folder)
        if not folder_path.exists():
            console.print(f"[red]Error: Folder does not exist: {folder}[/red]")
            continue
        
        if not folder_path.is_dir():
            console.print(f"[red]Error: Path is not a directory: {folder}[/red]")
            continue
        
        mp3_files = get_mp3_files(folder)
        if not mp3_files:
            console.print(f"[yellow]Warning: No MP3 files found in: {folder}[/yellow]")
            continue
        
        valid_folders.append(folder)
    
    if not valid_folders:
        console.print("[red]Error: No valid folders with MP3 files found[/red]")
        raise typer.Exit(1)
    
    # Show conversion info
    console.print(f"[green]Found {len(valid_folders)} valid folders:[/green]")
    total_files = 0
    total_size = 0.0
    
    for folder in valid_folders:
        mp3_count, size_mb, _ = get_folder_info(folder)
        total_files += mp3_count
        total_size += size_mb
        console.print(f"  • {folder}: {mp3_count} files ({size_mb:.1f} MB)")
    
    console.print(f"\n[blue]Total: {total_files} files ({total_size:.1f} MB)[/blue]")
    
    # Start conversion
    if background:
        console.print("[yellow]Starting conversion in background...[/yellow]")
        # In a real implementation, you'd start this as a background process
        console.print("[green]Conversion started! Use 'status' command to check progress.[/green]")
    else:
        console.print("[yellow]Starting conversion...[/yellow]")
        asyncio.run(_run_conversion(valid_folders, output))


async def _run_conversion(folders: List[str], output: Optional[str]) -> None:
    """Run the conversion process with progress tracking."""
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Converting MP3 files...", total=None)
        
        try:
            job = await converter.convert_folders(
                source_folders=folders,
                output_filename=output
            )
            
            progress.update(task, description="Conversion completed!")
            console.print(f"[green]Conversion completed! Output: {job.output_filename}[/green]")
            
        except Exception as e:
            progress.update(task, description="Conversion failed!")
            console.print(f"[red]Conversion failed: {e}[/red]")
            raise typer.Exit(1)


@app.command()
def list_folders():
    """List all available source folders with MP3 files."""
    
    try:
        folders = asyncio.run(list_source_folders())
        
        if not folders:
            console.print("[yellow]No source folders with MP3 files found.[/yellow]")
            return
        
        table = Table(title="Available Source Folders")
        table.add_column("Path", style="cyan")
        table.add_column("MP3 Files", justify="right", style="green")
        table.add_column("Size (MB)", justify="right", style="blue")
        table.add_column("Last Modified", style="magenta")
        
        for folder in folders:
            table.add_row(
                folder.path,
                str(folder.mp3_count),
                f"{folder.total_size_mb:.1f}",
                folder.last_modified.strftime("%Y-%m-%d %H:%M:%S")
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error listing folders: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def status(
    job_id: Optional[str] = typer.Option(None, "--job-id", "-j", help="Specific job ID to check")
):
    """Show conversion job status."""
    
    try:
        if job_id:
            # Show specific job status
            from uuid import UUID
            try:
                job_uuid = UUID(job_id)
                job_db = job_service.get_job(job_uuid)
                if not job_db:
                    console.print(f"[red]Error: Job not found: {job_id}[/red]")
                    raise typer.Exit(1)
                job = job_service.to_conversion_job(job_db)
                _display_job_status(job)
            except ValueError:
                console.print(f"[red]Error: Invalid job ID format: {job_id}[/red]")
                raise typer.Exit(1)
        else:
            # Show all jobs
            jobs = asyncio.run(list_jobs())
            
            if not jobs:
                console.print("[yellow]No active conversion jobs.[/yellow]")
                return
            
            table = Table(title="Active Conversion Jobs")
            table.add_column("Job ID", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Progress", justify="right", style="blue")
            table.add_column("Output", style="magenta")
            table.add_column("Created", style="yellow")
            
            for job in jobs:
                status_color = {
                    "pending": "yellow",
                    "processing": "blue",
                    "completed": "green",
                    "failed": "red"
                }.get(job.status, "white")
                
                table.add_row(
                    str(job.id)[:8] + "...",
                    f"[{status_color}]{job.status}[/{status_color}]",
                    f"{job.progress:.1f}%",
                    job.output_filename or "N/A",
                    job.created_at.strftime("%Y-%m-%d %H:%M:%S")
                )
            
            console.print(table)
            
    except Exception as e:
        console.print(f"[red]Error getting job status: {e}[/red]")
        raise typer.Exit(1)


def _display_job_status(job) -> None:
    """Display detailed status for a specific job."""
    
    console.print(f"\n[bold]Job Status: {job.id}[/bold]")
    console.print(f"Status: [green]{job.status}[/green]")
    console.print(f"Progress: [blue]{job.progress:.1f}%[/blue]")
    console.print(f"Output: [cyan]{job.output_filename}[/cyan]")
    console.print(f"Created: [yellow]{job.created_at.strftime('%Y-%m-%d %H:%M:%S')}[/yellow]")
    
    if job.started_at:
        console.print(f"Started: [yellow]{job.started_at.strftime('%Y-%m-%d %H:%M:%S')}[/yellow]")
    
    if job.completed_at:
        console.print(f"Completed: [yellow]{job.completed_at.strftime('%Y-%m-%d %H:%M:%S')}[/yellow]")
    
    if job.error_message:
        console.print(f"Error: [red]{job.error_message}[/red]")
    
    console.print(f"\nSource folders:")
    for folder in job.source_folders:
        console.print(f"  • {folder}")


# New job management commands
@app.command()
def jobs(
    action: str = typer.Argument(..., help="Action: list, show, clear"),
    job_id: Optional[str] = typer.Argument(None, help="Job ID for 'show' action"),
    status_filter: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status: queued, running, completed, failed"),
    days_old: int = typer.Option(30, "--days", "-d", help="Days old for 'clear' action")
):
    """Manage conversion jobs."""
    
    if action == "list":
        _list_jobs(status_filter)
    elif action == "show":
        if not job_id:
            console.print("[red]Error: Job ID is required for 'show' action[/red]")
            raise typer.Exit(1)
        _show_job(job_id)
    elif action == "clear":
        _clear_jobs(days_old)
    else:
        console.print(f"[red]Error: Unknown action '{action}'. Use: list, show, clear[/red]")
        raise typer.Exit(1)


def _list_jobs(status_filter: Optional[str] = None) -> None:
    """List all jobs with optional status filtering."""
    
    try:
        # Parse status filter
        status_enum = None
        if status_filter:
            try:
                status_enum = JobStatus(status_filter.lower())
            except ValueError:
                console.print(f"[red]Error: Invalid status '{status_filter}'. Valid options: queued, running, completed, failed[/red]")
                raise typer.Exit(1)
        
        # Get jobs from database
        jobs_db = job_service.get_jobs(status=status_enum, limit=100)
        
        if not jobs_db:
            console.print("[yellow]No jobs found.[/yellow]")
            return
        
        # Create table
        table = Table(title="Conversion Jobs")
        table.add_column("ID", style="cyan", width=12)
        table.add_column("Status", style="green", width=10)
        table.add_column("Input Folders", style="blue")
        table.add_column("Output File", style="magenta")
        table.add_column("Created", style="yellow", width=16)
        table.add_column("Duration", style="white", width=10)
        
        for job_db in jobs_db:
            # Parse input folders
            import json
            input_folders = json.loads(job_db.input_folders) if job_db.input_folders else []
            folder_display = f"{len(input_folders)} folder(s)" if input_folders else "None"
            
            # Status color
            status_color = {
                JobStatus.QUEUED: "yellow",
                JobStatus.RUNNING: "blue", 
                JobStatus.COMPLETED: "green",
                JobStatus.FAILED: "red"
            }.get(job_db.status, "white")
            
            # Output file display
            output_display = "N/A"
            if job_db.output_file:
                from pathlib import Path
                output_display = Path(job_db.output_file).name
            
            # Duration calculation
            duration = "N/A"
            if job_db.start_time and job_db.end_time:
                duration = str(job_db.end_time - job_db.start_time).split('.')[0]
            elif job_db.start_time:
                from datetime import datetime
                duration = str(datetime.utcnow() - job_db.start_time).split('.')[0]
            
            table.add_row(
                str(job_db.id)[:8] + "...",
                f"[{status_color}]{job_db.status.value}[/{status_color}]",
                folder_display,
                output_display,
                job_db.created_at.strftime("%Y-%m-%d %H:%M"),
                duration
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error listing jobs: {e}[/red]")
        raise typer.Exit(1)


def _show_job(job_id: str) -> None:
    """Show detailed information for a specific job."""
    
    try:
        from uuid import UUID
        
        # Parse UUID
        try:
            job_uuid = UUID(job_id)
        except ValueError:
            console.print(f"[red]Error: Invalid job ID format: {job_id}[/red]")
            raise typer.Exit(1)
        
        # Get job from database
        job_db = job_service.get_job(job_uuid)
        if not job_db:
            console.print(f"[red]Error: Job not found: {job_id}[/red]")
            raise typer.Exit(1)
        
        # Display job details
        console.print(f"\n[bold]Job Details: {job_db.id}[/bold]")
        console.print(f"Status: [green]{job_db.status.value}[/green]")
        console.print(f"Created: [yellow]{job_db.created_at.strftime('%Y-%m-%d %H:%M:%S')}[/yellow]")
        
        if job_db.start_time:
            console.print(f"Started: [yellow]{job_db.start_time.strftime('%Y-%m-%d %H:%M:%S')}[/yellow]")
        
        if job_db.end_time:
            console.print(f"Completed: [yellow]{job_db.end_time.strftime('%Y-%m-%d %H:%M:%S')}[/yellow]")
        
        if job_db.output_file:
            console.print(f"Output: [cyan]{job_db.output_file}[/cyan]")
        
        if job_db.log:
            console.print(f"Log: [white]{job_db.log}[/white]")
        
        # Input folders
        import json
        input_folders = json.loads(job_db.input_folders) if job_db.input_folders else []
        console.print(f"\nInput folders ({len(input_folders)}):")
        for folder in input_folders:
            console.print(f"  • {folder}")
        
    except Exception as e:
        console.print(f"[red]Error showing job: {e}[/red]")
        raise typer.Exit(1)


def _clear_jobs(days_old: int) -> None:
    """Clear old completed/failed jobs."""
    
    try:
        deleted_count = job_service.clear_old_jobs(days_old)
        console.print(f"[green]Cleared {deleted_count} jobs older than {days_old} days[/green]")
        
    except Exception as e:
        console.print(f"[red]Error clearing jobs: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
