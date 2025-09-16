# Database Documentation

## Overview

AIOM4B uses SQLite as its database with SQLModel as the ORM for persistent job tracking. The database stores job records with comprehensive metadata including status, input/output information, and timestamps.

## Database Schema

### Jobs Table

The `jobs` table stores all conversion job records:

```sql
CREATE TABLE jobs (
    id UUID PRIMARY KEY,
    status VARCHAR(20) NOT NULL DEFAULT 'queued',
    input_folders TEXT NOT NULL,
    output_file TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    log TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### Field Descriptions

- **id**: UUID primary key, auto-generated for each job
- **status**: Job status enum (`queued`, `running`, `completed`, `failed`)
- **input_folders**: JSON string containing list of input folder paths
- **output_file**: Path to the generated .m4b file (null until completion)
- **start_time**: When the job started processing (null until started)
- **end_time**: When the job completed or failed (null until finished)
- **log**: Error messages or additional information (optional)
- **created_at**: Job creation timestamp
- **updated_at**: Last modification timestamp

## ORM Models

### JobDB (SQLModel)

```python
class JobDB(SQLModel, table=True):
    """Database model for conversion jobs."""

    __tablename__ = "jobs"

    id: UUID = SQLField(primary_key=True, default_factory=uuid4)
    status: JobStatus = SQLField(default=JobStatus.QUEUED)
    input_folders: str = SQLField(description="JSON string of input folders")
    output_file: Optional[str] = SQLField(default=None, description="Path to generated .m4b")
    start_time: Optional[datetime] = SQLField(default=None)
    end_time: Optional[datetime] = SQLField(default=None)
    log: Optional[str] = SQLField(default=None, description="Error/info messages")
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)
```

### JobStatus Enum

```python
class JobStatus(str, Enum):
    """Job status enumeration."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
```

## Database Configuration

### Connection

- **Database URL**: `sqlite:///{DATA_DIR}/aiom4b.db`
- **Location**: `data/aiom4b.db` (relative to project root)
- **Engine**: SQLite with WAL mode for better concurrency

### Optimizations

The database is configured with SQLite-specific optimizations:

```python
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for better performance."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=1000")
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.close()
```

## Migration Strategy

### Initial Setup

The database is automatically initialized on application startup:

```python
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on application startup."""
    create_db_and_tables()
```

### Schema Changes

For future schema changes:

1. **Add new fields**: SQLModel will automatically add new columns
2. **Modify existing fields**: Use Alembic for proper migrations
3. **Remove fields**: Create migration scripts to handle data migration

### Backup Strategy

- Database file: `data/aiom4b.db`
- Backup location: `data/backup/`
- Recommended: Regular automated backups before schema changes

## Job Service

### JobService Class

The `JobService` class provides database operations:

```python
class JobService:
    def create_job(self, job_data: JobCreate) -> JobDB
    def get_job(self, job_id: UUID) -> Optional[JobDB]
    def get_jobs(self, status: Optional[JobStatus] = None, limit: int = 50, offset: int = 0) -> List[JobDB]
    def update_job(self, job_id: UUID, job_update: JobUpdate) -> Optional[JobDB]
    def delete_job(self, job_id: UUID) -> bool
    def clear_old_jobs(self, days_old: int = 30) -> int
    def to_conversion_job(self, job_db: JobDB) -> ConversionJob
```

### Key Operations

- **Create**: Insert new job records
- **Read**: Query jobs with filtering and pagination
- **Update**: Modify job status and metadata
- **Delete**: Remove job records
- **Cleanup**: Remove old completed/failed jobs

## Data Flow

1. **Job Creation**: API/CLI creates job → Database insert
2. **Job Processing**: Converter updates status → Database update
3. **Job Completion**: Final status and output path → Database update
4. **Job Querying**: API/CLI/UI reads jobs → Database select
5. **Job Cleanup**: Periodic cleanup → Database delete

## Performance Considerations

- **Indexing**: UUID primary key provides fast lookups
- **Pagination**: Large job lists use LIMIT/OFFSET
- **Cleanup**: Old jobs are periodically removed to maintain performance
- **WAL Mode**: Better concurrency for read/write operations

## Security

- **File Permissions**: Database file should be readable/writable by application only
- **SQL Injection**: SQLModel provides protection through parameterized queries
- **Data Validation**: Pydantic models validate all input data

## Monitoring

- **Database Size**: Monitor `aiom4b.db` file size
- **Job Count**: Track total jobs and status distribution
- **Performance**: Monitor query execution times
- **Errors**: Log database connection and query errors
