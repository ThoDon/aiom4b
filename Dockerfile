FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy poetry files
COPY pyproject.toml poetry.lock* ./

# Configure poetry and install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-dev

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data/source /app/data/output /app/data/backup

# Expose port
EXPOSE 8000

# Run the application
CMD ["poetry", "run", "uvicorn", "aiom4b.main:app", "--host", "0.0.0.0", "--port", "8000"]
