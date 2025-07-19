# Dockerfile for DigitalOcean Droplet deployment
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_NO_INTERACTION=1
ENV POETRY_VENV_IN_PROJECT=1
ENV POETRY_CACHE_DIR=/tmp/poetry_cache

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Set work directory
WORKDIR /app

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-root

# Copy project
COPY cv_project/ ./cv_project/
COPY docker-entrypoint-droplet.sh ./
COPY nginx.conf /etc/nginx/sites-available/default
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Make entrypoint executable
RUN chmod +x docker-entrypoint-droplet.sh

# Create directories
RUN mkdir -p /app/staticfiles /app/mediafiles /var/log/gunicorn /var/log/celery

# Collect static files
WORKDIR /app/cv_project
RUN poetry run python manage.py collectstatic --noinput --settings=core.droplet_settings || true

# Expose ports
EXPOSE 80 8000

# Set the working directory back to /app
WORKDIR /app

RUN mkdir -p /var/log/nginx && touch /var/log/nginx/access.log /var/log/nginx/error.log

# Use droplet entrypoint
ENTRYPOINT ["./docker-entrypoint-droplet.sh"]