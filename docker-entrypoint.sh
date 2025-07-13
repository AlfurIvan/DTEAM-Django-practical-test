#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐳 Starting CV Project Docker Container...${NC}"

# Python-based service waiting (no nc required)
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3

    echo -e "${YELLOW}⏳ Waiting for $service_name at $host:$port...${NC}"

    python -c "
import socket
import time
import sys

def wait_for_port(host, port, timeout=60):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, int(port)))
            sock.close()
            if result == 0:
                return True
            time.sleep(1)
        except Exception:
            time.sleep(1)
    return False

if not wait_for_port('$host', $port):
    print('Timeout waiting for $service_name')
    sys.exit(1)
"

    echo -e "${GREEN}✅ $service_name is up and running!${NC}"
}

# Wait for PostgreSQL
if [ "$DATABASE_HOST" ]; then
    wait_for_service $DATABASE_HOST ${DATABASE_PORT:-5432} "PostgreSQL"
fi

# Wait for Redis
if [ "$REDIS_URL" ]; then
    # Extract host and port from Redis URL
    REDIS_HOST=$(echo $REDIS_URL | cut -d'/' -f3 | cut -d':' -f1)
    REDIS_PORT=$(echo $REDIS_URL | cut -d'/' -f3 | cut -d':' -f2)
    wait_for_service $REDIS_HOST ${REDIS_PORT:-6379} "Redis"
fi

echo -e "${BLUE}🔧 Running database migrations...${NC}"
python manage.py makemigrations --noinput
python manage.py migrate --noinput

echo -e "${BLUE}📊 Collecting static files...${NC}"
python manage.py collectstatic --noinput --clear

# Load initial data if it exists and database is empty
echo -e "${BLUE}📝 Checking for initial data...${NC}"
python manage.py shell -c "
from main.models import CV
if CV.objects.count() == 0:
    print('Loading initial data...')
    from django.core.management import call_command
    try:
        call_command('loaddata', 'initial_data')
        print('✅ Initial data loaded successfully!')
    except Exception as e:
        print(f'⚠️  Could not load initial data: {e}')
else:
    print('📊 Database already has data, skipping initial data load.')
"

# Create superuser if it doesn't exist (for development)
if [ "$DEBUG" = "True" ]; then
    echo -e "${BLUE}👤 Creating development superuser...${NC}"
    python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('✅ Superuser created: admin/admin123')
else:
    print('👤 Superuser already exists')
"
fi

echo -e "${GREEN}🚀 Starting application...${NC}"
echo -e "${BLUE}📍 Application will be available at: http://localhost:8000${NC}"
echo -e "${BLUE}🔧 Admin panel: http://localhost:8000/admin (admin/admin123)${NC}"
echo -e "${BLUE}🔌 API: http://localhost:8000/api/${NC}"
echo -e "${BLUE}📊 Settings: http://localhost:8000/settings/${NC}"
echo -e "${BLUE}📋 Logs: http://localhost:8000/logs/${NC}"

# Execute the main command
exec "$@"