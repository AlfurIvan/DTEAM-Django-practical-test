#!/bin/bash

# setup-droplet.sh
# Automated setup script for DigitalOcean Droplet deployment

set -e

echo "🚀 Starting CV Management System Droplet Setup..."
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root"
   exit 1
fi

# Get user inputs
read -p "Enter your GitHub username: " GITHUB_USER
read -p "Enter your email address: " USER_EMAIL
read -p "Enter your domain name (optional, press enter to skip): " DOMAIN_NAME
read -s -p "Enter your OpenAI API key: " OPENAI_KEY
echo
read -s -p "Enter your Gmail app password: " GMAIL_PASSWORD
echo

# Step 1: Update system
print_header "1. Updating system packages..."
apt update && apt upgrade -y
print_status "System updated successfully"

# Step 2: Install essential packages
print_header "2. Installing essential packages..."
apt install -y curl wget git ufw fail2ban htop sysstat iotop nethogs
print_status "Essential packages installed"

# Step 3: Configure firewall
print_header "3. Configuring firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80
ufw allow 443
ufw --force enable
print_status "Firewall configured"

# Step 4: Install Docker
print_header "4. Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    print_status "Docker installed successfully"
else
    print_status "Docker already installed"
fi

# Step 5: Install Docker Compose
print_header "5. Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    print_status "Docker Compose installed successfully"
else
    print_status "Docker Compose already installed"
fi

# Step 6: Configure fail2ban
print_header "6. Configuring fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban
print_status "Fail2ban configured"

# Step 7: Clone repository
print_header "7. Cloning repository..."
cd /opt
if [ -d "DTEAM-Django-practical-test" ]; then
    print_warning "Repository already exists, pulling latest changes..."
    cd DTEAM-Django-practical-test
    git pull origin main
else
    git clone https://github.com/${GITHUB_USER}/DTEAM-Django-practical-test.git
    cd DTEAM-Django-practical-test
fi
print_status "Repository ready"

# Step 8: Create directories
print_header "8. Creating necessary directories..."
mkdir -p logs backups
print_status "Directories created"

# Step 9: Generate environment file
print_header "9. Generating environment configuration..."
DROPLET_IP=$(curl -s http://checkip.amazonaws.com/)
SECRET_KEY=$(python3 -c 'import secrets; import string; print("".join(secrets.choice(string.ascii_letters + string.digits + "!@#$%^&*") for _ in range(50)))')

cat > .env << EOF
# Django settings
DEBUG=False
SECRET_KEY=${SECRET_KEY}
DJANGO_SETTINGS_MODULE=core.droplet_settings

# Server settings
DROPLET_IP=${DROPLET_IP}
DOMAIN_NAME=${DOMAIN_NAME}

# Database settings
DATABASE_NAME=cv_project_db
DATABASE_USER=cv_project_user
DATABASE_PASSWORD=$(openssl rand -base64 32)

# Redis settings
REDIS_PASSWORD=$(openssl rand -base64 32)

# Email settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=${USER_EMAIL}
EMAIL_HOST_PASSWORD=${GMAIL_PASSWORD}
EMAIL_FROM=${USER_EMAIL}

# OpenAI settings
OPENAI_API_KEY=${OPENAI_KEY}

# SSL settings
USE_HTTPS=False
EOF

print_status "Environment file created"

# Step 10: Set up backup scripts
print_header "10. Setting up backup scripts..."

# Database backup script
cat > /opt/backup-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)
PROJECT_DIR="/opt/DTEAM-Django-practical-test"

mkdir -p $BACKUP_DIR
cd $PROJECT_DIR

# Database backup
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U cv_project_user cv_project_db > $BACKUP_DIR/db_backup_$DATE.sql

# Static files backup
tar -czf $BACKUP_DIR/static_backup_$DATE.tar.gz staticfiles/ mediafiles/ 2>/dev/null || true

# Environment backup
cp .env $BACKUP_DIR/env_backup_$DATE

# Cleanup old backups (keep 7 days)
find $BACKUP_DIR -name "*backup_*" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /opt/backup-db.sh

# Health check script
cat > /opt/health-check.sh << EOF
#!/bin/bash
WEBSITE="http://${DROPLET_IP}"
EMAIL="${USER_EMAIL}"

if ! curl -f \$WEBSITE > /dev/null 2>&1; then
    echo "Website is down!" | mail -s "CV Project Alert" \$EMAIL
    docker-compose -f /opt/DTEAM-Django-practical-test/docker-compose.prod.yml restart web
fi
EOF

chmod +x /opt/health-check.sh

print_status "Backup scripts created"

# Step 11: Set up cron jobs
print_header "11. Setting up automated tasks..."

# Add cron jobs
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/backup-db.sh") | crontab -
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/health-check.sh") | crontab -

print_status "Automated tasks configured"

# Step 12: Deploy application
print_header "12. Building and deploying application..."
docker-compose -f docker-compose.prod.yml up --build -d

print_status "Application deployed!"

# Step 13: Wait for services to start
print_header "13. Waiting for services to start..."
sleep 30

# Check if services are running
if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    print_status "Services are running successfully!"
else
    print_error "Some services failed to start. Check logs with: docker-compose -f docker-compose.prod.yml logs"
fi

# Step 14: Display summary
print_header "🎉 Deployment Summary"
echo "================================================"
echo -e "✅ Application URL: ${GREEN}http://${DROPLET_IP}${NC}"
echo -e "✅ Admin Panel: ${GREEN}http://${DROPLET_IP}/admin/${NC}"
echo -e "✅ API Documentation: ${GREEN}http://${DROPLET_IP}/api/${NC}"
echo -e "✅ Admin Credentials: ${YELLOW}admin / admin123${NC}"

if [ -n "$DOMAIN_NAME" ]; then
    echo -e "✅ Domain: ${GREEN}http://${DOMAIN_NAME}${NC} (after DNS propagation)"
fi

echo ""
echo "📋 Next Steps:"
echo "1. Configure your domain's DNS to point to ${DROPLET_IP}"
echo "2. Set up SSL certificate with: certbot --nginx -d ${DOMAIN_NAME}"
echo "3. Update USE_HTTPS=True in .env after SSL setup"
echo "4. Monitor logs with: docker-compose -f docker-compose.prod.yml logs -f"
echo ""
echo "📁 Important Locations:"
echo "   - Project: /opt/DTEAM-Django-practical-test"
echo "   - Logs: /opt/DTEAM-Django-practical-test/logs"
echo "   - Backups: /opt/backups"
echo ""
echo "🔧 Useful Commands:"
echo "   - View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "   - Restart: docker-compose -f docker-compose.prod.yml restart"
echo "   - Update: git pull && docker-compose -f docker-compose.prod.yml up --build -d"
echo ""
print_status "Setup completed successfully! 🚀"