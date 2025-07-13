FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_NO_INTERACTION=1
ENV POETRY_VENV_IN_PROJECT=1
ENV POETRY_CACHE_DIR=/tmp/poetry_cache

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        netcat-openbsd \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry

# Set work directory
WORKDIR /app

# Copy poetry files
COPY pyproject.toml poetry.lock* ./

# Configure poetry and install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --only=main --no-root\
    && rm -rf $POETRY_CACHE_DIR

# Copy project
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p /app/logs \
    && mkdir -p /app/cv_project/staticfiles \
    && mkdir -p /app/cv_project/media \
    && chmod -R 755 /app

# Expose port
EXPOSE 8000

# Default working directory
WORKDIR /app/cv_project

# Default command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]