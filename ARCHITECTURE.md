# AIOM4B Architecture

## Overview

AIOM4B is a Python 3.12 application that converts MP3 files to M4B format using FFmpeg. It provides both a CLI interface and a REST API for managing conversion jobs, with persistent job tracking using SQLite database.

## Project Structure

```
aiom4b/
├── aiom4b/                 # Main application package
│   ├── __init__.py        # Package initialization
│   ├── main.py            # FastAPI application entry point
│   ├── api.py             # REST API routes
│   ├── cli.py             # CLI interface using Typer
│   ├── converter.py       # MP3 to M4B conversion logic
│   ├── models.py          # Pydantic and SQLModel data models
│   ├── config.py          # Configuration settings
│   ├── database.py        # SQLite database configuration
│   ├── job_service.py     # Job management service
│   └── utils.py           # Utility functions
├── data/                  # Application data directory
│   ├── output/           # Converted M4B files
│   ├── backup/           # Backup files with timestamps
│   └── aiom4b.db         # SQLite database file
├── source/               # Source MP3 folders
├── web-ui/               # Next.js web interface
│   ├── app/              # Next.js app directory
│   ├── components/       # React components
│   └── lib/              # API client and utilities
├── pyproject.toml        # Poetry configuration
├── Dockerfile           # Docker container configuration
├── docker-compose.yml   # Docker Compose configuration
└── README.md           # Project documentation
```

## Core Components

### 1. FastAPI Application (`main.py`)

- Main web application entry point
- Database initialization on startup
- CORS middleware for web UI integration
- Health check endpoints
- API documentation at `/docs`

### 2. REST API (`api.py`)

- **GET /api/v1/folders** - List available source folders
- **POST /api/v1/convert** - Start conversion job
- **POST /api/v1/jobs** - Create new job
- **GET /api/v1/jobs/{job_id}** - Get job details
- **GET /api/v1/jobs** - List jobs with filtering and pagination
- **DELETE /api/v1/jobs/{job_id}** - Delete job record
- **POST /api/v1/jobs/clear** - Clear old jobs
- **GET /api/v1/download/{job_id}** - Download converted file

### 3. CLI Interface (`cli.py`)

- **convert** - Convert MP3 folders to M4B
- **list** - Show available source folders
- **status** - Display job status and progress
- **jobs** - Comprehensive job management (list, show, clear)

### 4. Conversion Engine (`converter.py`)

- `MP3ToM4BConverter` class handles the conversion process
- Uses FFmpeg for audio processing
- Supports multiple CPU cores for faster processing
- Job management with status tracking
- Error handling and progress reporting

### 5. Data Models (`models.py`)

- `JobDB` - SQLModel database model for persistent storage
- `ConversionJob` - Pydantic model for API responses
- `SourceFolder` - Folder information
- `ConversionRequest` - API request model
- `JobCreate` - Job creation model
- `JobUpdate` - Job update model
- `JobListResponse` - Paginated job list response
- `JobResponse` - API response model
- `JobStatus` enum for job states

### 6. Database Layer (`database.py`)

- SQLite database configuration
- SQLModel ORM setup
- Database session management
- Connection optimization (WAL mode, pragmas)
- Automatic table creation

### 7. Job Service (`job_service.py`)

- Database operations for job management
- CRUD operations for job records
- Job filtering and pagination
- Data conversion between database and API models
- Cleanup operations for old jobs

### 8. Configuration (`config.py`)

- Environment-based configuration
- Directory structure setup
- Processing settings (CPU usage, file limits)
- Backup configuration

### 9. Utilities (`utils.py`)

- File system operations
- MP3 file discovery
- Backup creation
- File size formatting
- Filename sanitization

### 10. Web UI (`web-ui/`)

- Next.js 15 React application
- TypeScript for type safety
- Tailwind CSS for styling
- React Query for API state management
- Job management dashboard
- Real-time job status updates

## Dependencies

### Core Dependencies

- **FastAPI** - Web framework for REST API
- **Typer** - CLI framework with rich output
- **FFmpeg-Python** - Python bindings for FFmpeg
- **Pydantic** - Data validation and serialization
- **SQLModel** - SQL ORM with Pydantic integration
- **Uvicorn** - ASGI server for FastAPI
- **Rich** - Terminal formatting and progress bars

### Development Dependencies

- **Poetry** - Dependency management and packaging
- **Docker** - Containerization
- **Pytest** - Testing framework
- **Black** - Code formatting
- **MyPy** - Type checking

## Design Decisions

### 1. Async/Await Pattern

- FastAPI uses async for better performance
- FFmpeg operations run in subprocess for non-blocking execution
- Job status tracking without blocking the main thread

### 2. Job Management

- UUID-based job identification
- SQLite database for persistent job storage
- Status tracking: queued → running → completed/failed
- Progress reporting for long-running operations
- Job filtering, pagination, and cleanup operations
- Database-backed job history and analytics

### 3. File Organization

- Separate directories for source, output, and backup
- Timestamped backups for safety
- Recursive MP3 file discovery
- Automatic directory creation

### 4. Error Handling

- Comprehensive exception handling
- User-friendly error messages
- Graceful degradation on failures
- Detailed logging for debugging

### 5. Performance Optimization

- Multi-core CPU utilization for FFmpeg
- Efficient file discovery with pathlib
- Minimal memory usage for large file sets
- Background job processing

## Security Considerations

- Input validation for file paths
- Filename sanitization
- CORS configuration for web UI
- File size limits to prevent abuse
- Backup retention policies

## Scalability

- Stateless API design
- SQLite database for job persistence
- Horizontal scaling with load balancers
- Database-backed job storage and history
- Queue system integration ready (Celery/RQ)
- Container-based deployment
- Web UI for better user experience

## Monitoring and Observability

- Health check endpoints
- Job status tracking
- Error logging and reporting
- Performance metrics collection
- API documentation with examples
