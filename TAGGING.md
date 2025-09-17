# Tagging System Documentation

## Overview

The AIOM4B tagging system allows you to automatically tag converted M4B files with metadata from Audible's API. This includes book titles, authors, narrators, series information, descriptions, cover art, and more.

## Features

- **Automatic Detection**: Automatically detects untagged M4B files in your output directory
- **Audible API Integration**: Searches Audible's official API for book metadata
- **Manual Search**: Allows custom search queries for better matching
- **Comprehensive Metadata**: Tags files with title, author, narrator, series, description, cover art, and more
- **Background Processing**: Tagging jobs run in the background with progress tracking
- **Web UI Integration**: Full web interface for managing tagging operations
- **CLI Support**: Command-line interface for tagging operations

## Workflow

### 1. File Detection

- The system automatically scans the output directory for M4B files
- Untagged files are identified and listed in the tagging interface
- Files are tracked in the database with their current tagging status

### 2. Metadata Search

- **Automatic Search**: System attempts to extract title/author from filename
- **Manual Search**: Users can input custom search queries
- **Multiple Locales**: Searches across different Audible locales (US, UK, CA, FR, DE, etc.)

### 3. Metadata Application

- Users select the correct match from search results
- System fetches detailed book information from Audible API
- Metadata is applied to the M4B file using mutagen
- Cover art is downloaded and embedded
- File is marked as tagged in the database

## API Endpoints

### File Management

- `GET /api/v1/files/untagged` - List all untagged M4B files
- `DELETE /api/v1/files/{file_id}` - Delete a tagged file record

### Search Operations

- `POST /api/v1/files/{file_id}/search?query={query}` - Search Audible API
- `POST /api/v1/files/{file_id}/apply?asin={asin}` - Apply metadata to file

### Job Management

- `POST /api/v1/jobs/tagging` - Create a tagging job
- `GET /api/v1/jobs/tagging` - List all tagging jobs
- `GET /api/v1/jobs/tagging/{job_id}` - Get tagging job details

## CLI Commands

### File Management

```bash
# List all converted files with tag status
aiom4b files list

# Search Audible API for a specific file
aiom4b files search <file_id> --query "book title author"

# Start tagging process for a file
aiom4b files tag <file_id>
```

### Job Management

```bash
# List all jobs (including tagging jobs)
aiom4b jobs list

# Show specific job details
aiom4b jobs show <job_id>

# Clear old jobs
aiom4b jobs clear --days 30
```

## Web UI Features

### Tagging Tab

- **File List**: Shows all converted but untagged files
- **Search Interface**: Manual search with custom queries
- **Result Selection**: Choose from multiple search results
- **Progress Tracking**: Real-time job status updates
- **File Management**: Delete untagged files if needed

### Jobs Tab

- **Tagging Jobs**: View all tagging jobs alongside conversion jobs
- **Progress Monitoring**: Real-time progress bars and status updates
- **Error Handling**: Display error messages for failed jobs
- **Job History**: Track completed and failed tagging attempts

## Database Schema

### TaggedFileDB Table

```sql
CREATE TABLE tagged_files (
    id UUID PRIMARY KEY,
    file_path TEXT NOT NULL,
    asin TEXT,
    title TEXT,
    author TEXT,
    narrator TEXT,
    series TEXT,
    series_part TEXT,
    description TEXT,
    cover_url TEXT,
    cover_path TEXT,
    is_tagged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### JobDB Table (Extended)

```sql
-- Added job_type column to existing jobs table
ALTER TABLE jobs ADD COLUMN job_type TEXT DEFAULT 'conversion';
```

## Configuration

### Audible API Settings

- **Locales**: Configurable list of Audible locales to search
- **Search Limits**: Maximum number of results per search
- **Timeout**: API request timeout settings
- **User Agent**: Browser user agent for API requests

### Tagging Settings

- **Backup Creation**: Create backups before tagging (enabled by default)
- **Cover Embedding**: Embed cover art in M4B files
- **Metadata Creation**: Create additional metadata files (desc.txt, reader.txt, .opf)
- **Series in Filename**: Include series information in filenames

## Error Handling

### Common Issues

1. **API Rate Limiting**: System handles rate limits with retry logic
2. **Network Errors**: Graceful fallback for network connectivity issues
3. **File Permissions**: Proper error messages for file access issues
4. **Invalid Metadata**: Validation of metadata before application

### Troubleshooting

- Check file permissions for M4B files
- Verify network connectivity for Audible API access
- Review job logs for detailed error information
- Ensure sufficient disk space for cover art downloads

## Performance Considerations

### Optimization

- **Background Processing**: Tagging jobs run asynchronously
- **Caching**: Search results are cached to reduce API calls
- **Batch Operations**: Multiple files can be processed efficiently
- **Progress Tracking**: Real-time updates without blocking UI

### Limitations

- **API Rate Limits**: Audible API has rate limiting
- **File Size**: Large M4B files may take longer to process
- **Network Dependency**: Requires internet connection for metadata fetching

## Security

### Data Protection

- **No Personal Data**: Only book metadata is stored
- **Local Processing**: All file operations happen locally
- **API Keys**: No API keys required (uses public Audible API)
- **File Access**: Only reads/writes to designated directories

## Future Enhancements

### Planned Features

- **Batch Tagging**: Tag multiple files simultaneously
- **Custom Metadata**: Allow manual metadata entry
- **Metadata Validation**: Verify metadata accuracy
- **Export Options**: Export metadata to various formats
- **Integration**: Better integration with audiobook management software

### API Improvements

- **Caching Layer**: Implement Redis caching for better performance
- **Webhook Support**: Real-time notifications for job completion
- **Bulk Operations**: Support for bulk file operations
- **Advanced Search**: More sophisticated search algorithms

## Support

### Getting Help

- Check the job logs for detailed error information
- Review the API documentation for endpoint details
- Use the CLI help commands for usage information
- Check the web UI for real-time status updates

### Reporting Issues

- Include job IDs and error messages
- Provide file paths and metadata information
- Include system information and logs
- Describe the expected vs actual behavior
