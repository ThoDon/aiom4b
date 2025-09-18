# AIOM4B API Documentation

## Overview

AIOM4B provides both a REST API and CLI interface for MP3 to M4B conversion. This document covers all available endpoints, CLI commands, and usage examples.

## REST API

### Base URL

```
http://localhost:8000/api/v1
```

### Authentication

Currently no authentication is required. In production, implement proper API key or JWT authentication.

### Endpoints

## Conversion Endpoints

#### 1. List Source Folders

**GET** `/folders`

Returns all available source folders containing MP3 files.

**Response:**

```json
[
  {
    "path": "/path/to/folder1",
    "mp3_count": 15,
    "total_size_mb": 245.7,
    "last_modified": "2024-01-15T10:30:00"
  },
  {
    "path": "/path/to/folder2",
    "mp3_count": 8,
    "total_size_mb": 128.3,
    "last_modified": "2024-01-14T15:45:00"
  }
]
```

**Example:**

```bash
curl -X GET "http://localhost:8000/api/v1/folders"
```

#### 2. Start Conversion

**POST** `/convert`

Start MP3 to M4B conversion jobs. Each folder is treated as a separate unit and creates its own job and M4B file.

**Request Body:**

```json
{
  "folder_conversions": {
    "/path/to/folder1": "book1.m4b",
    "/path/to/folder2": "book2.m4b",
    "/path/to/folder3": null
  }
}
```

**Response:**

```json
[
  {
    "job_id": "123e4567-e89b-12d3-a456-426614174000",
    "status": "queued",
    "message": "Conversion job started with ID: 123e4567-e89b-12d3-a456-426614174000"
  },
  {
    "job_id": "9876543-e89b-12d3-a456-426614174001",
    "status": "queued",
    "message": "Conversion job started with ID: 9876543-e89b-12d3-a456-426614174001"
  },
  {
    "job_id": "4567890-e89b-12d3-a456-426614174002",
    "status": "queued",
    "message": "Conversion job started with ID: 4567890-e89b-12d3-a456-426614174002"
  }
]
```

**Examples:**

```bash
# Conversion with custom filenames for each folder
curl -X POST "http://localhost:8000/api/v1/convert" \
  -H "Content-Type: application/json" \
  -d '{
    "folder_conversions": {
      "/path/to/folder1": "book1.m4b",
      "/path/to/folder2": "book2.m4b"
    }
  }'

# Conversion with auto-generated filenames (null values)
curl -X POST "http://localhost:8000/api/v1/convert" \
  -H "Content-Type: application/json" \
  -d '{
    "folder_conversions": {
      "/path/to/folder1": null,
      "/path/to/folder2": null
    }
  }'

# Mixed: some custom, some auto-generated
curl -X POST "http://localhost:8000/api/v1/convert" \
  -H "Content-Type: application/json" \
  -d '{
    "folder_conversions": {
      "/path/to/folder1": "my_custom_book.m4b",
      "/path/to/folder2": null
    }
  }'
```

**Filename Handling:**

- **Custom filename**: Provide the desired filename as the value
- **Auto-generated**: Use `null` as the value to auto-generate a filename based on the folder name

#### 2.1. Create Job

**POST** `/jobs`

Create a new conversion job (alternative to `/convert`).

**Request Body:**

```json
{
  "input_folders": ["/path/to/folder1", "/path/to/folder2"]
}
```

**Response:**

```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "queued",
  "message": "Job created with ID: 123e4567-e89b-12d3-a456-426614174000"
}
```

**Example:**

```bash
curl -X POST "http://localhost:8000/api/v1/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "input_folders": ["/path/to/folder1", "/path/to/folder2"]
  }'
```

#### 3. Get Job Status

**GET** `/jobs/{job_id}`

Get the current status of a conversion job.

**Response:**

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "source_folders": ["/path/to/folder1", "/path/to/folder2"],
  "output_filename": "my_audiobook.m4b",
  "status": "running",
  "created_at": "2024-01-15T10:30:00",
  "started_at": "2024-01-15T10:30:05",
  "completed_at": null,
  "error_message": null,
  "progress": 45.5,
  "output_path": "/app/data/readyToTag/my_audiobook.m4b"
}
```

**Example:**

```bash
curl -X GET "http://localhost:8000/api/v1/jobs/123e4567-e89b-12d3-a456-426614174000"
```

#### 4. List All Jobs

**GET** `/jobs`

Get all conversion jobs with optional filtering and pagination.

**Query Parameters:**

- `status` - Filter by job status (`queued`, `running`, `completed`, `failed`)
- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 50, max: 100)

**Response:**

```json
{
  "jobs": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "source_folders": ["/path/to/folder1"],
      "output_filename": "book1.m4b",
      "status": "completed",
      "created_at": "2024-01-15T10:30:00",
      "started_at": "2024-01-15T10:30:05",
      "completed_at": "2024-01-15T10:35:00",
      "error_message": null,
      "progress": 100.0,
      "output_path": "/app/data/output/book1.m4b"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 50
}
```

**Examples:**

```bash
# Get all jobs
curl -X GET "http://localhost:8000/api/v1/jobs"

# Filter by status
curl -X GET "http://localhost:8000/api/v1/jobs?status=completed"

# Pagination
curl -X GET "http://localhost:8000/api/v1/jobs?page=2&per_page=10"
```

#### 5. Download Converted File

**GET** `/download/{job_id}`

Download the converted M4B file.

**Response:** Binary file download

**Example:**

```bash
curl -X GET "http://localhost:8000/api/v1/download/123e4567-e89b-12d3-a456-426614174000" \
  -o "my_audiobook.m4b"
```

#### 6. Delete Job

**DELETE** `/jobs/{job_id}`

Delete a job record from the database.

**Response:**

```json
{
  "message": "Job 123e4567-e89b-12d3-a456-426614174000 deleted successfully"
}
```

**Example:**

```bash
curl -X DELETE "http://localhost:8000/api/v1/jobs/123e4567-e89b-12d3-a456-426614174000"
```

#### 7. Clear Old Jobs

**POST** `/jobs/clear`

Remove old completed/failed jobs from the database.

**Query Parameters:**

- `days_old` - Remove jobs older than this many days (default: 30, max: 365)

**Response:**

```json
{
  "message": "Cleared 5 old jobs"
}
```

**Example:**

```bash
curl -X POST "http://localhost:8000/api/v1/jobs/clear?days_old=7"
```

## File Management Endpoints

#### 1. List Processing Files

**GET** `/files/processing`

Returns all files currently being converted (in processing/ folder).

**Response:**

```json
[
  {
    "filename": "book1_20240115_103000.m4b",
    "path": "/app/data/processing/book1_20240115_103000.m4b",
    "size_mb": 245.7,
    "created_at": "2024-01-15T10:30:00"
  }
]
```

**Example:**

```bash
curl -X GET "http://localhost:8000/api/v1/files/processing"
```

#### 2. List Ready Files

**GET** `/files/ready`

Returns all converted files waiting for tagging (in readyToTag/ folder).

**Response:**

```json
[
  {
    "filename": "book1_20240115_103000.m4b",
    "path": "/app/data/readyToTag/book1_20240115_103000.m4b",
    "size_mb": 245.7,
    "created_at": "2024-01-15T10:30:00"
  }
]
```

**Example:**

```bash
curl -X GET "http://localhost:8000/api/v1/files/ready"
```

## CLI Commands

### Installation

```bash
# Install dependencies
poetry install

# Run CLI
poetry run python -m aiom4b.cli --help
```

### Commands

#### 1. Convert

Convert MP3 files from folders to M4B format.

**Usage:**

```bash
poetry run python -m aiom4b.cli convert [FOLDERS...] [OPTIONS]
```

**Arguments:**

- `FOLDERS` - One or more source folders containing MP3 files

**Options:**

- `--output, -o` - Output filename (optional)
- `--background, -b` - Run in background mode

**Examples:**

```bash
# Convert single folder
poetry run python -m aiom4b.cli convert /path/to/audiobook

# Convert multiple folders
poetry run python -m aiom4b.cli convert /path/to/book1 /path/to/book2

# Specify output filename
poetry run python -m aiom4b.cli convert /path/to/audiobook --output "my_book.m4b"

# Run in background
poetry run python -m aiom4b.cli convert /path/to/audiobook --background
```

#### 2. List Folders

List all available source folders with MP3 files.

**Usage:**

```bash
poetry run python -m aiom4b.cli list
```

**Example:**

```bash
poetry run python -m aiom4b.cli list
```

**Output:**

```
Available Source Folders
┌─────────────────────────┬───────────┬──────────┬─────────────────────┐
│ Path                    │ MP3 Files │ Size (MB)│ Last Modified       │
├─────────────────────────┼───────────┼──────────┼─────────────────────┤
│ /path/to/folder1        │ 15        │ 245.7    │ 2024-01-15 10:30:00 │
│ /path/to/folder2        │ 8         │ 128.3    │ 2024-01-14 15:45:00 │
└─────────────────────────┴───────────┴──────────┴─────────────────────┘
```

#### 3. Status

Show conversion job status and progress.

**Usage:**

```bash
poetry run python -m aiom4b.cli status [OPTIONS]
```

**Options:**

- `--job-id, -j` - Check specific job ID

**Examples:**

```bash
# Show all jobs
poetry run python -m aiom4b.cli status

# Show specific job
poetry run python -m aiom4b.cli status --job-id 123e4567-e89b-12d3-a456-426614174000
```

**Output:**

```
Active Conversion Jobs
┌─────────────┬──────────┬──────────┬─────────────────┬─────────────────────┐
│ Job ID      │ Status   │ Progress │ Output          │ Created             │
├─────────────┼──────────┼──────────┼─────────────────┼─────────────────────┤
│ 123e4567... │ running  │ 45.5%    │ my_book.m4b    │ 2024-01-15 10:30:00 │
└─────────────┴──────────┴──────────┴─────────────────┴─────────────────────┘
```

#### 4. Jobs Management

Manage conversion jobs with comprehensive job tracking.

**Usage:**

```bash
poetry run python -m aiom4b.cli jobs <ACTION> [OPTIONS]
```

**Actions:**

- `list` - List all jobs with optional filtering
- `show <job_id>` - Show detailed information for a specific job
- `clear` - Clear old completed/failed jobs

**Options:**

- `--status, -s` - Filter by status (`queued`, `running`, `completed`, `failed`)
- `--days, -d` - Days old for clear action (default: 30)

**Examples:**

```bash
# List all jobs
poetry run python -m aiom4b.cli jobs list

# List only completed jobs
poetry run python -m aiom4b.cli jobs list --status completed

# Show specific job details
poetry run python -m aiom4b.cli jobs show 123e4567-e89b-12d3-a456-426614174000

# Clear jobs older than 7 days
poetry run python -m aiom4b.cli jobs clear --days 7
```

**List Output:**

```
Conversion Jobs
┌─────────────┬──────────┬─────────────────┬─────────────────┬─────────────────┬──────────┐
│ ID          │ Status   │ Input Folders   │ Output File     │ Created         │ Duration │
├─────────────┼──────────┼─────────────────┼─────────────────┼─────────────────┼──────────┤
│ 123e4567... │ completed│ 2 folder(s)     │ book1.m4b       │ 2024-01-15 10:30│ 0:05:23  │
│ 9876543...  │ running  │ 1 folder(s)     │ book2.m4b       │ 2024-01-15 11:00│ 0:02:15  │
└─────────────┴──────────┴─────────────────┴─────────────────┴─────────────────┴──────────┘
```

**Show Output:**

```
Job Details: 123e4567-e89b-12d3-a456-426614174000
Status: completed
Created: 2024-01-15 10:30:00
Started: 2024-01-15 10:30:05
Completed: 2024-01-15 10:35:28
Output: /app/data/output/book1.m4b

Input folders (2):
  • /path/to/folder1
  • /path/to/folder2
```

## Tagging Endpoints

### 1. List Untagged Files

**GET** `/files/untagged`

Returns all converted but untagged M4B files.

**Query Parameters:**

- `page` (optional) - Page number (default: 1)
- `per_page` (optional) - Items per page (default: 50, max: 100)

**Response:**

```json
{
  "files": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "file_path": "/path/to/output/book1.m4b",
      "asin": null,
      "title": null,
      "author": null,
      "narrator": null,
      "series": null,
      "series_part": null,
      "description": null,
      "cover_url": null,
      "cover_path": null,
      "is_tagged": false,
      "created_at": "2024-01-15T10:30:00",
      "updated_at": "2024-01-15T10:30:00"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 50
}
```

**Example:**

```bash
curl -X GET "http://localhost:8000/api/v1/files/untagged?page=1&per_page=10"
```

### 2. Create Tagging Job

**POST** `/jobs/tagging`

Creates a new tagging job for a file.

**Request Body:**

```json
{
  "file_path": "/path/to/output/book1.m4b",
  "asin": "B08N5WRWNW"
}
```

**Response:**

```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "queued",
  "message": "Tagging job started with ID: 123e4567-e89b-12d3-a456-426614174000"
}
```

**Example:**

```bash
curl -X POST "http://localhost:8000/api/v1/jobs/tagging" \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/path/to/output/book1.m4b"}'
```

### 3. Search Audible API

**POST** `/files/{file_id}/search`

Search Audible API for metadata using a query.

**Query Parameters:**

- `query` (required) - Search query string

**Response:**

```json
[
  {
    "title": "The Great Book",
    "author": "John Author",
    "narrator": "Jane Narrator",
    "series": "Great Series",
    "asin": "B08N5WRWNW",
    "locale": "com"
  }
]
```

**Example:**

```bash
curl -X POST "http://localhost:8000/api/v1/files/123e4567-e89b-12d3-a456-426614174000/search?query=The Great Book"
```

### 4. Apply Metadata to File

**POST** `/files/{file_id}/apply`

Apply selected metadata to a file.

**Query Parameters:**

- `asin` (required) - ASIN of the book to apply

**Response:**

```json
{
  "message": "Metadata applied successfully"
}
```

**Example:**

```bash
curl -X POST "http://localhost:8000/api/v1/files/123e4567-e89b-12d3-a456-426614174000/apply?asin=B08N5WRWNW"
```

### 5. List Tagging Jobs

**GET** `/jobs/tagging`

Returns all tagging jobs.

**Response:**

```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "file_path": "/path/to/output/book1.m4b",
    "status": "completed",
    "created_at": "2024-01-15T10:30:00",
    "started_at": "2024-01-15T10:30:05",
    "completed_at": "2024-01-15T10:35:28",
    "error_message": null,
    "progress": 100.0,
    "metadata": null
  }
]
```

**Example:**

```bash
curl -X GET "http://localhost:8000/api/v1/jobs/tagging"
```

### 6. Get Tagging Job Details

**GET** `/jobs/tagging/{job_id}`

Returns detailed information about a specific tagging job.

**Response:**

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "file_path": "/path/to/output/book1.m4b",
  "status": "completed",
  "created_at": "2024-01-15T10:30:00",
  "started_at": "2024-01-15T10:30:05",
  "completed_at": "2024-01-15T10:35:28",
  "error_message": null,
  "progress": 100.0,
  "metadata": null
}
```

**Example:**

```bash
curl -X GET "http://localhost:8000/api/v1/jobs/tagging/123e4567-e89b-12d3-a456-426614174000"
```

### 7. Delete Tagged File

**DELETE** `/files/{file_id}`

Delete a tagged file record.

**Response:**

```json
{
  "message": "File 123e4567-e89b-12d3-a456-426614174000 deleted successfully"
}
```

**Example:**

```bash
curl -X DELETE "http://localhost:8000/api/v1/files/123e4567-e89b-12d3-a456-426614174000"
```

## Tagging CLI Commands

### 1. List Files

**Usage:**

```bash
poetry run python -m aiom4b.cli files list
```

**Output:**

```
Converted Files
┌─────────────┬─────────────────┬─────────┬─────────────┬─────────────┬─────────────────┐
│ ID          │ Filename        │ Tagged  │ Title       │ Author      │ Created         │
├─────────────┼─────────────────┼─────────┼─────────────┼─────────────┼─────────────────┤
│ 123e4567... │ book1.m4b       │ ❌ No   │ Unknown     │ Unknown     │ 2024-01-15 10:30│
│ 9876543...  │ book2.m4b       │ ✅ Yes  │ The Great   │ John Author │ 2024-01-15 11:00│
└─────────────┴─────────────────┴─────────┴─────────────┴─────────────┴─────────────────┘
```

### 2. Search Audible

**Usage:**

```bash
poetry run python -m aiom4b.cli files search <file_id> --query "search query"
```

**Example:**

```bash
poetry run python -m aiom4b.cli files search 123e4567-e89b-12d3-a456-426614174000 --query "The Great Book"
```

**Output:**

```
Searching Audible for: The Great Book

Audible Search Results
┌───────┬─────────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│ Index │ Title           │ Author      │ Narrator    │ Series      │ ASIN        │
├───────┼─────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ 1     │ The Great Book  │ John Author │ Jane Narrator│ Great Series│ B08N5WRWNW  │
└───────┴─────────────────┴─────────────┴─────────────┴─────────────┴─────────────┘

Found 1 results. Use 'files tag 123e4567-e89b-12d3-a456-426614174000' to apply metadata.
```

### 3. Tag File

**Usage:**

```bash
poetry run python -m aiom4b.cli files tag <file_id>
```

**Example:**

```bash
poetry run python -m aiom4b.cli files tag 123e4567-e89b-12d3-a456-426614174000
```

**Output:**

```
Tagging job started with ID: 123e4567-e89b-12d3-a456-426614174000
File: book1.m4b
Use 'jobs list' to check progress.
```

## Error Handling

### HTTP Status Codes

- `200` - Success
- `400` - Bad Request (invalid input)
- `404` - Not Found (job/folder not found)
- `500` - Internal Server Error

### Error Response Format

```json
{
  "detail": "Error message description"
}
```

### Common Errors

- **Folder not found**: Source folder path doesn't exist
- **No MP3 files**: Folder contains no MP3 files
- **Job not found**: Invalid job ID
- **Conversion failed**: FFmpeg processing error
- **File not found**: Output file missing or deleted

## Rate Limiting

Currently no rate limiting is implemented. Consider adding rate limiting for production use:

- Maximum concurrent jobs per user
- Request rate limiting
- File size limits

## WebSocket Support (Future)

Consider adding WebSocket support for real-time job progress updates:

```javascript
const ws = new WebSocket(
  "ws://localhost:8000/ws/jobs/123e4567-e89b-12d3-a456-426614174000"
);
ws.onmessage = (event) => {
  const progress = JSON.parse(event.data);
  console.log(`Progress: ${progress.percentage}%`);
};
```
