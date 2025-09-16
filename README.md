# AIOM4B - MP3 to M4B Conversion Application

A modern Python application that converts MP3 files to M4B format using FFmpeg, providing both CLI and REST API interfaces with a web UI.

## Features

- 🎵 **MP3 to M4B Conversion**: High-quality audio conversion using FFmpeg
- 📁 **Multiple Folder Support**: Process multiple source folders simultaneously
- 🔄 **Recursive Processing**: Automatically discovers MP3 files in subdirectories
- 💾 **Backup Safety**: Creates timestamped backups before processing
- 🚀 **High Performance**: Utilizes all available CPU cores for faster conversion
- 🌐 **REST API**: Full REST API for integration with other applications
- 💻 **CLI Interface**: Rich command-line interface with progress tracking
- 🎨 **Web UI**: Modern web interface built with Next.js 15
- 📊 **Job Management**: Track conversion jobs with real-time status updates
- 🐳 **Docker Support**: Containerized deployment with Docker

## Quick Start

### Prerequisites

- Python 3.12+
- FFmpeg installed on your system
- Node.js 18+ (for web UI)
- Poetry (for Python dependency management)

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd aiom4b
   ```

2. **Install Python dependencies**

   ```bash
   poetry install
   ```

3. **Install system dependencies**

   ```bash
   # macOS
   brew install ffmpeg

   # Ubuntu/Debian
   sudo apt-get install ffmpeg

   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

4. **Run the application**

   ```bash
   # Easy startup (recommended)
   ./start.sh

   # Or manually:
   # Start the API server
   poetry run uvicorn aiom4b.main:app --reload

   # Start the web UI (in another terminal)
   cd web-ui && npm install && npm run dev

   # Or use Docker
   docker-compose up
   ```

5. **Test the application**

   ```bash
   # Run the test script to verify everything is working
   python test_conversion.py
   ```

### CLI Usage

```bash
# List available source folders
poetry run python -m aiom4b.cli list

# Convert MP3 files to M4B
poetry run python -m aiom4b.cli convert /path/to/audiobook

# Convert multiple folders
poetry run python -m aiom4b.cli convert /path/to/book1 /path/to/book2

# Check conversion status
poetry run python -m aiom4b.cli status
```

### API Usage

```bash
# List source folders
curl http://localhost:8000/api/v1/folders

# Start conversion
curl -X POST http://localhost:8000/api/v1/convert \
  -H "Content-Type: application/json" \
  -d '{"source_folders": ["/path/to/audiobook"], "output_filename": "my_book.m4b"}'

# Check job status
curl http://localhost:8000/api/v1/jobs/{job_id}

# Download converted file
curl http://localhost:8000/api/v1/download/{job_id} -o my_book.m4b
```

## Web UI

The web interface provides a modern, responsive UI for managing conversions:

- 📁 **Folder Management**: Browse and select source folders
- 🎯 **Job Creation**: Start new conversion jobs with custom settings
- 📊 **Progress Tracking**: Real-time job status and progress updates
- 📥 **File Download**: Download converted M4B files directly
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile

### Web UI Setup

```bash
# Navigate to web UI directory
cd web-ui

# Install dependencies
npm install

# Start development server
npm run dev
```

## Project Structure

```
aiom4b/
├── aiom4b/                 # Python application
│   ├── main.py            # FastAPI app
│   ├── api.py             # REST API routes
│   ├── cli.py             # CLI interface
│   ├── converter.py       # Conversion logic
│   ├── models.py          # Data models
│   ├── config.py          # Configuration
│   └── utils.py           # Utilities
├── web-ui/                # Next.js web interface
├── data/                  # Application data
│   ├── output/           # Converted files
│   ├── backup/           # Backup files
│   └── logs/             # Log files
├── source/               # Source MP3 folders
├── docs/                 # Documentation
├── pyproject.toml        # Python dependencies
├── Dockerfile           # Docker configuration
└── docker-compose.yml   # Docker Compose
```

## Configuration

### Environment Variables

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

### Directory Structure

- `source/` - Place your MP3 folders here
- `data/output/` - Converted M4B files are saved here
- `data/backup/` - Automatic backups are stored here
- `data/logs/` - Application logs

## Docker Deployment

### Using Docker Compose

```bash
# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

### Using Docker

```bash
# Build the image
docker build -t aiom4b .

# Run the container
docker run -p 8000:8000 -v $(pwd)/data:/app/data -v $(pwd)/source:/app/source aiom4b
```

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **API Reference**: See [API.md](API.md)

## Documentation

- [Architecture](ARCHITECTURE.md) - System architecture and design decisions
- [API Reference](API.md) - Complete API and CLI documentation
- [Workflow](WORKFLOW.md) - End-to-end conversion process
- [UI Documentation](UI.md) - Web interface documentation

## Development

### Setup Development Environment

```bash
# Install development dependencies
poetry install --with dev

# Run tests
poetry run pytest

# Format code
poetry run black aiom4b/
poetry run isort aiom4b/

# Type checking
poetry run mypy aiom4b/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📧 **Email**: support@aiom4b.com
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-org/aiom4b/issues)
- 📖 **Documentation**: [Project Wiki](https://github.com/your-org/aiom4b/wiki)

## Changelog

### v0.1.0

- Initial release
- MP3 to M4B conversion
- CLI and REST API interfaces
- Web UI with Next.js 15
- Docker support
- Comprehensive documentation
