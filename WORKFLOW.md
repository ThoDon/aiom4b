# AIOM4B Workflow Documentation

## End-to-End Conversion Process

This document describes the complete workflow from input MP3 folders to output M4B files, including the backup process and error handling.

## 1. Input Phase

### 1.1 Source Folder Discovery

- User provides one or more folder paths containing MP3 files
- System recursively scans each folder for MP3 files
- Validates folder existence and accessibility
- Counts MP3 files and calculates total size

### 1.2 Validation

- **Folder Validation**: Ensures all provided paths exist and are directories
- **File Validation**: Confirms MP3 files are present and accessible
- **Size Validation**: Checks total file size against configured limits
- **Format Validation**: Verifies all files are valid MP3 format

### 1.3 Pre-Processing

- Sorts MP3 files alphabetically for consistent ordering
- Creates job record with unique UUID
- Generates output filename if not provided
- Initializes progress tracking

## 2. Backup Phase

### 2.1 Backup Creation

- **Automatic Backup**: Creates timestamped backup before processing
- **Backup Location**: `data/backup/{folder_name}_{timestamp}/`
- **Backup Contents**: Complete folder structure with all files
- **Backup Metadata**: Records backup creation time and source

### 2.2 Backup Safety

- **Atomic Operation**: Backup creation is atomic (all-or-nothing)
- **Space Check**: Verifies sufficient disk space for backup
- **Integrity Check**: Validates backup completeness
- **Retention Policy**: Configurable backup retention period

### 2.3 Backup Structure

```
data/backup/
├── audiobook1_20240115_103000/
│   ├── chapter01.mp3
│   ├── chapter02.mp3
│   └── metadata.txt
├── audiobook2_20240115_104500/
│   ├── track01.mp3
│   └── track02.mp3
└── cleanup_log.txt
```

## 3. Conversion Phase

### 3.1 Job Initialization

- **Status Update**: Changes job status to "processing"
- **Start Time**: Records processing start timestamp
- **Resource Allocation**: Allocates CPU cores for FFmpeg
- **Progress Reset**: Initializes progress to 0%

### 3.2 FFmpeg Processing

- **Input Preparation**: Creates FFmpeg input streams for all MP3 files
- **Audio Configuration**:
  - Codec: AAC
  - Bitrate: 128k
  - Channels: Stereo (2)
  - Sample Rate: 44.1kHz
- **CPU Optimization**: Uses all available CPU cores
- **Output Generation**: Creates single M4B file

### 3.3 Progress Tracking

- **Real-time Updates**: Monitors FFmpeg output for progress
- **Status Reporting**: Updates job progress percentage
- **Error Detection**: Captures and reports FFmpeg errors
- **Timeout Handling**: Implements processing timeouts

### 3.4 Quality Assurance

- **Output Validation**: Verifies M4B file creation
- **File Integrity**: Checks output file completeness
- **Size Verification**: Confirms expected file size
- **Audio Quality**: Validates audio stream integrity

## 4. Output Phase

### 4.1 File Organization

- **Output Location**: `data/output/{filename}.m4b`
- **Naming Convention**: Sanitized, timestamped filenames
- **Metadata Preservation**: Maintains original file metadata
- **Access Permissions**: Sets appropriate file permissions

### 4.2 Job Completion

- **Status Update**: Changes job status to "completed"
- **Completion Time**: Records processing end timestamp
- **Progress Finalization**: Sets progress to 100%
- **Output Path**: Records final file location

### 4.3 Cleanup

- **Temporary Files**: Removes intermediate processing files
- **Resource Release**: Frees allocated system resources
- **Job Archival**: Moves completed job to archive
- **Log Rotation**: Manages log file sizes

## 5. Error Handling

### 5.1 Error Categories

- **Input Errors**: Invalid folders, missing files, permission issues
- **Processing Errors**: FFmpeg failures, resource exhaustion
- **Output Errors**: File system issues, disk space problems
- **System Errors**: Hardware failures, network issues

### 5.2 Error Recovery

- **Automatic Retry**: Retries failed operations with backoff
- **Graceful Degradation**: Continues processing other files
- **Error Reporting**: Detailed error messages and logs
- **Rollback Support**: Restores from backup on critical failures

### 5.3 Error States

- **Job Status**: "failed" with error message
- **Error Logging**: Detailed error information
- **User Notification**: Clear error descriptions
- **Recovery Options**: Suggested remediation steps

## 6. Monitoring and Logging

### 6.1 Job Monitoring

- **Real-time Status**: Live job status updates
- **Progress Tracking**: Percentage completion
- **Performance Metrics**: Processing speed, resource usage
- **Health Checks**: System health monitoring

### 6.2 Logging

- **Structured Logs**: JSON-formatted log entries
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log Rotation**: Automatic log file management
- **Log Aggregation**: Centralized logging for multiple instances

### 6.3 Metrics Collection

- **Processing Time**: Job duration tracking
- **File Sizes**: Input/output size metrics
- **Success Rates**: Conversion success statistics
- **Resource Usage**: CPU, memory, disk utilization

## 7. Configuration Management

### 7.1 Environment Variables

```bash
# Application Settings
DEBUG=false
API_HOST=0.0.0.0
API_PORT=8000

# Processing Settings
MAX_CONCURRENT_JOBS=4
USE_ALL_CPUS=true
MAX_FILE_SIZE_MB=1000

# Backup Settings
BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=30
```

### 7.2 Directory Structure

```
aiom4b/
├── data/
│   ├── output/          # Converted M4B files
│   ├── backup/          # Backup files
│   └── logs/            # Application logs
├── source/              # Source MP3 folders
└── config/              # Configuration files
```

## 8. Performance Optimization

### 8.1 CPU Utilization

- **Multi-core Processing**: Uses all available CPU cores
- **Parallel Processing**: Concurrent job processing
- **Resource Management**: Efficient resource allocation
- **Load Balancing**: Distributes processing load

### 8.2 Memory Management

- **Streaming Processing**: Processes files in chunks
- **Memory Monitoring**: Tracks memory usage
- **Garbage Collection**: Automatic memory cleanup
- **Memory Limits**: Configurable memory constraints

### 8.3 I/O Optimization

- **Async I/O**: Non-blocking file operations
- **Buffer Management**: Optimized buffer sizes
- **Disk Caching**: Intelligent disk caching
- **Network Optimization**: Efficient API responses

## 9. Security Considerations

### 9.1 Input Validation

- **Path Sanitization**: Prevents directory traversal
- **File Type Validation**: Ensures only MP3 files
- **Size Limits**: Prevents resource exhaustion
- **Permission Checks**: Validates file access rights

### 9.2 Output Security

- **Filename Sanitization**: Prevents malicious filenames
- **Access Control**: Restricts file access
- **Audit Logging**: Tracks all operations
- **Data Encryption**: Optional file encryption

## 10. Troubleshooting

### 10.1 Common Issues

- **FFmpeg Not Found**: Install FFmpeg system dependency
- **Permission Denied**: Check file/folder permissions
- **Disk Space**: Ensure sufficient disk space
- **Memory Issues**: Monitor memory usage

### 10.2 Debug Mode

```bash
# Enable debug logging
export DEBUG=true

# Run with verbose output
poetry run python -m aiom4b.cli convert /path/to/folder --verbose
```

### 10.3 Log Analysis

- **Error Patterns**: Identify common error patterns
- **Performance Issues**: Analyze processing times
- **Resource Usage**: Monitor system resources
- **User Behavior**: Track usage patterns
