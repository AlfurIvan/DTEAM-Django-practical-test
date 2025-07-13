# Docker Setup for CV Project

This guide will help you set up the CV Project using Docker with PostgreSQL and Redis.

## 🐳 Prerequisites

- **Docker Desktop** installed and running
- **Docker Compose** (included with Docker Desktop)
- **Git** for version control

## 🚀 Quick Start

### 1. Clone and Navigate
```bash
git clone https://github.com/AlfurIvan/DTEAM-Django-practical-test.git
cd DTEAM-Django-practical-test
```

### 2. Environment Setup
```bash
# Copy the environment file (it's already configured)
cp .env.example .env  
# OR the .env file is already included
```

### 3. Build and Start Services
```bash
# Build and start all services
docker-compose up --build

# OR run in background
docker-compose up --build -d
```

### 4. Access the Application
- **Web App**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin (admin/admin123)
- **API**: http://localhost:8000/api/
- **Settings**: http://localhost:8000/settings/
- **Logs**: http://localhost:8000/logs/

## 🏗️ Services Overview

### Core Services
- **web**: Django application (port 8000)
- **db**: PostgreSQL 16 database (port 5432)
- **redis**: Redis cache/broker (port 6379)
- **celery**: Celery worker (Windows-compatible with eventlet)
- **celery-beat**: Celery scheduler

### Service Health Checks
All services include health checks to ensure proper startup order.

## 📝 Environment Variables

Edit `.env` file to configure:

```bash
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database
DATABASE_NAME=cv_project_db
DATABASE_USER=cv_project_user
DATABASE_PASSWORD=cv_project_password_123

# Redis & Celery
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# OpenAI (for future tasks)
OPENAI_API_KEY=your-openai-api-key-here
```

## 🛠️ Docker Commands

### Basic Operations
```bash
# Start services
docker-compose up

# Start in background
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs

# View logs for specific service
docker-compose logs web
docker-compose logs celery
```

### Development Commands
```bash
# Run Django commands
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py shell
docker-compose exec web python manage.py test --settings=core.test_settings
# Create superuser
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic
```

### Database Operations
```bash
# Access PostgreSQL shell
docker-compose exec db psql -U cv_project_user -d cv_project_db

# Backup database
docker-compose exec db pg_dump -U cv_project_user cv_project_db > backup.sql

# Restore database
docker-compose exec -T db psql -U cv_project_user -d cv_project_db < backup.sql
```

### Redis Operations
```bash
# Access Redis CLI
docker-compose exec redis redis-cli

# Monitor Redis
docker-compose exec redis redis-cli monitor
```

## 🔧 Troubleshooting

### Service Won't Start
```bash
# Check service status
docker-compose ps

# View service logs
docker-compose logs [service_name]

# Restart specific service
docker-compose restart [service_name]
```

### Database Connection Issues
```bash
# Check if PostgreSQL is ready
docker-compose exec db pg_isready -U cv_project_user

# Reset database
docker-compose down -v  # ⚠️ This deletes all data!
docker-compose up --build
```

### Permission Issues (Windows)
```bash
# If you get permission errors, try:
docker-compose down
docker system prune -f
docker-compose up --build
```

### Celery Issues
```bash
# Check Celery worker status
docker-compose logs celery

# Restart Celery
docker-compose restart celery
```

## 📊 Data Persistence

### Volumes
- `postgres_data`: PostgreSQL data
- `redis_data`: Redis data  
- `static_volume`: Django static files
- `media_volume`: Django media files

### Backup Data
```bash
# Backup all volumes
docker run --rm -v cv_project_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .
```

## 🧪 Testing with Docker

```bash
# Run tests
docker-compose exec web python manage.py test

# Run specific test
docker-compose exec web python manage.py test main.tests.RequestLogModelTest

# Run with test settings
docker-compose exec web python manage.py test --settings=core.test_settings
```

## 🚦 Development vs Production

### Development (Current Setup)
- DEBUG=True
- SQLite fallback for non-Docker development
- Auto-reload enabled
- Development superuser created automatically

### Production Considerations
- Set DEBUG=False
- Use proper SECRET_KEY
- Configure ALLOWED_HOSTS
- Use SSL/TLS
- Set up proper logging
- Use production WSGI server (gunicorn)

## 🔄 Migration from SQLite

If you have existing SQLite data:

```bash
# Dump SQLite data
python manage.py dumpdata > data.json

# Start Docker services
docker-compose up -d

# Load data into PostgreSQL
docker-compose exec web python manage.py loaddata data.json
```

## 📦 Project Structure
```
DTEAM-Django-practical-test/
├── docker-compose.yml          # Docker services configuration
├── Dockerfile                  # Django app container
├── docker-entrypoint.sh       # Container startup script
├── .env                        # Environment variables
├── cv_project/                 # Django project
│   ├── manage.py
│   ├── core/
│   └── main/
└── README_Docker.md           # This file
```

## 🎯 Next Steps

1. ✅ Services are running
2. ✅ Database is migrated
3. ✅ Redis is connected
4. ✅ Celery workers are ready
5. 🔄 Ready for Task 7 (Celery implementation)
6. 🔄 Ready for Task 8 (OpenAI integration)

## 💡 Tips

- **Windows Users**: The setup uses `eventlet` for Celery Windows compatibility
- **Port Conflicts**: If ports 8000, 5432, or 6379 are in use, change them in `docker-compose.yml`
- **Performance**: Use `docker-compose up -d` to run in background
- **Debugging**: Use `docker-compose logs -f` to follow logs in real-time