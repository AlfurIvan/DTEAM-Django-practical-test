#!/bin/bash

# docker-entrypoint-droplet.sh
# Production entrypoint for DigitalOcean Droplet

set -e

cd /app/cv_project

echo "Starting droplet deployment..."

# Wait for database to be ready
echo "Waiting for database..."
until poetry run python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.droplet_settings')
django.setup()
from django.db import connection
connection.ensure_connection()
print('Database is ready!')
"; do
    echo "Database is unavailable - sleeping"
    sleep 2
done

echo "Database is ready!"

# Run migrations
echo "Running database migrations..."
poetry run python manage.py migrate --settings=core.droplet_settings --noinput

# Collect static files
echo "Collecting static files..."
poetry run python manage.py collectstatic --noinput --settings=core.droplet_settings

# Load initial data if needed (only on first deployment)
echo "Loading initial data..."
poetry run python manage.py loaddata initial_data --settings=core.droplet_settings || echo "Initial data already loaded or not needed"

# Create superuser if needed
echo "Creating superuser..."
poetry run python manage.py shell --settings=core.droplet_settings << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
EOF

# Create log directory
mkdir -p /var/log

echo "Starting services..."

# Start supervisor to manage nginx and gunicorn
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf