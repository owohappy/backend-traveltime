#!/bin/bash

# TravelTime Backend Production Deployment Script with SSL
# This script handles the complete production deployment including SSL setup

set -e  # Exit on any error

echo "=== TravelTime Backend Production Deployment ==="
echo "$(date): Starting production deployment with SSL support"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running as root or with sudo access
if [ "$EUID" -eq 0 ]; then
    print_warning "Running as root. This is not recommended for production."
    SUDO=""
else
    SUDO="sudo"
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo "=== System Requirements Check ==="
echo ""

# Check Docker
if command_exists docker; then
    print_status "Docker is installed: $(docker --version)"
else
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check Docker Compose
if command_exists docker-compose; then
    print_status "Docker Compose is installed: $(docker-compose --version)"
elif docker compose version >/dev/null 2>&1; then
    print_status "Docker Compose (v2) is installed: $(docker compose version)"
    alias docker-compose='docker compose'
else
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if ports are available
if $SUDO netstat -tuln | grep -q ':80 '; then
    print_warning "Port 80 is already in use. This may conflict with nginx."
    print_info "Current processes using port 80:"
    $SUDO netstat -tulnp | grep ':80 '
    echo ""
    read -p "Continue anyway? (y/N): " continue_port80
    if [[ ! $continue_port80 =~ ^[Yy]$ ]]; then
        print_error "Deployment cancelled due to port conflict."
        exit 1
    fi
fi

if $SUDO netstat -tuln | grep -q ':443 '; then
    print_warning "Port 443 is already in use. This may conflict with nginx SSL."
    print_info "Current processes using port 443:"
    $SUDO netstat -tulnp | grep ':443 '
    echo ""
    read -p "Continue anyway? (y/N): " continue_port443
    if [[ ! $continue_port443 =~ ^[Yy]$ ]]; then
        print_error "Deployment cancelled due to port conflict."
        exit 1
    fi
fi

echo ""
echo "=== Environment Configuration ==="
echo ""

# Check if .env file exists, create if not
if [ ! -f ".env" ]; then
    print_info "Creating production environment file..."
    cat > .env << EOF
# TravelTime Backend Production Environment
APP_DEBUG=false
APP_BASE_URL=https://tt.owohappy.com
JWT_SECRET_KEY=$(openssl rand -hex 32)
EMAIL_ENABLED=false

# Database settings
DB_PATH=/app/db/traveltime.db

# Logging
LOG_LEVEL=INFO
LOG_PATH=/app/log
EOF
    print_status "Environment file created at .env"
else
    print_status "Environment file already exists"
fi

echo ""
echo "=== SSL Certificate Setup ==="
echo ""

# Check if SSL certificates exist
if [ -f "ssl/cert.pem" ] && [ -f "ssl/key.pem" ]; then
    print_status "SSL certificates found"
    
    # Validate certificates
    if openssl x509 -in ssl/cert.pem -text -noout > /dev/null 2>&1; then
        print_status "SSL certificate is valid"
        
        # Check expiration
        if openssl x509 -checkend $((7*24*60*60)) -noout -in ssl/cert.pem; then
            print_status "SSL certificate is valid for more than 7 days"
        else
            print_warning "SSL certificate expires within 7 days"
            print_info "Certificate expiry date:"
            openssl x509 -in ssl/cert.pem -noout -dates | grep notAfter
        fi
    else
        print_error "SSL certificate is invalid or corrupted"
        exit 1
    fi
    
    if openssl rsa -in ssl/key.pem -check -noout > /dev/null 2>&1; then
        print_status "SSL private key is valid"
    else
        print_error "SSL private key is invalid or corrupted"
        exit 1
    fi
else
    print_warning "SSL certificates not found"
    echo ""
    echo "Would you like to set up SSL certificates now?"
    echo "1) Yes, run SSL setup (Recommended)"
    echo "2) No, continue without SSL (HTTP only)"
    echo "3) Exit and set up SSL manually"
    echo ""
    read -p "Enter your choice (1-3): " ssl_choice
    
    case $ssl_choice in
        1)
            print_info "Running SSL setup script..."
            if [ -f "./setup_ssl.sh" ]; then
                chmod +x ./setup_ssl.sh
                ./setup_ssl.sh
                if [ $? -ne 0 ]; then
                    print_error "SSL setup failed. Please check the error messages above."
                    exit 1
                fi
            else
                print_error "SSL setup script not found. Please run it manually first."
                exit 1
            fi
            ;;
        2)
            print_warning "Continuing without SSL. The site will be accessible via HTTP only."
            print_warning "This is NOT recommended for production use."
            ;;
        3)
            print_info "Please set up SSL certificates and run this script again."
            echo ""
            echo "Quick SSL setup options:"
            echo "1. Run: ./setup_ssl.sh"
            echo "2. Place certificates manually in ssl/cert.pem and ssl/key.pem"
            echo ""
            exit 0
            ;;
        *)
            print_error "Invalid choice. Exiting."
            exit 1
            ;;
    esac
fi

echo ""
echo "=== Database Preparation ==="
echo ""

# Create database directory if it doesn't exist
mkdir -p db

# Check if production database exists
if [ -f "db/traveltime.db" ]; then
    print_status "Production database found"
    
    # Create backup
    backup_name="db/traveltime_backup_$(date +%Y%m%d_%H%M%S).db"
    cp "db/traveltime.db" "$backup_name"
    print_status "Database backed up to $backup_name"
else
    print_info "Production database not found, will be created automatically"
fi

echo ""
echo "=== Docker Deployment ==="
echo ""

# Stop any existing containers
print_info "Stopping existing containers..."
docker-compose down 2>/dev/null || true

# Pull latest images
print_info "Pulling latest images..."
docker-compose pull

# Build the application
print_info "Building application..."
docker-compose build --no-cache

# Start services
print_info "Starting services..."
docker-compose up -d

# Wait for services to start
print_info "Waiting for services to start..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    print_status "Services started successfully"
else
    print_error "Failed to start services"
    print_info "Service status:"
    docker-compose ps
    print_info "Logs:"
    docker-compose logs --tail=20
    exit 1
fi

echo ""
echo "=== Health Checks ==="
echo ""

# Wait for API to be ready
print_info "Waiting for API to be ready..."
for i in {1..30}; do
    if curl -f -s http://localhost:8000/ping > /dev/null 2>&1; then
        print_status "API is responding"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "API failed to respond after 30 attempts"
        print_info "API logs:"
        docker-compose logs api --tail=20
        exit 1
    fi
    sleep 2
done

# Test nginx
print_info "Testing nginx configuration..."
if docker-compose exec -T nginx nginx -t; then
    print_status "Nginx configuration is valid"
else
    print_error "Nginx configuration test failed"
    docker-compose logs nginx --tail=20
    exit 1
fi

# Test HTTP redirect (if SSL is configured)
if [ -f "ssl/cert.pem" ] && [ -f "ssl/key.pem" ]; then
    print_info "Testing HTTP to HTTPS redirect..."
    if curl -s -I http://localhost | grep -q "301\|302"; then
        print_status "HTTP to HTTPS redirect is working"
    else
        print_warning "HTTP to HTTPS redirect may not be working correctly"
    fi
    
    # Test HTTPS (if certificates are self-signed, ignore certificate errors)
    print_info "Testing HTTPS connection..."
    if curl -k -s -I https://localhost > /dev/null 2>&1; then
        print_status "HTTPS is working"
    else
        print_warning "HTTPS connection failed"
    fi
fi

echo ""
echo "=== Final Status ==="
echo ""

# Display service status
print_info "Service Status:"
docker-compose ps

echo ""
print_info "Service URLs:"
echo "  HTTP:  http://tt.owohappy.com"
if [ -f "ssl/cert.pem" ] && [ -f "ssl/key.pem" ]; then
    echo "  HTTPS: https://tt.owohappy.com"
fi
echo "  Local API: http://localhost:8000"

echo ""
print_info "Useful Commands:"
echo "  View logs:           docker-compose logs -f"
echo "  Restart services:    docker-compose restart"
echo "  Stop services:       docker-compose down"
echo "  Update application:  docker-compose build --no-cache && docker-compose up -d"
echo "  SSL renewal:         ./renew_ssl.sh"

echo ""
print_info "Monitoring:"
echo "  Health check:        curl http://localhost:8000/ping"
echo "  SSL check:           curl -I https://tt.owohappy.com"
echo "  Certificate expiry:  openssl x509 -in ssl/cert.pem -noout -dates"

echo ""
if [ -f "ssl/cert.pem" ] && [ -f "ssl/key.pem" ]; then
    print_status "🎉 Production deployment with SSL completed successfully!"
    echo ""
    print_info "Security Recommendations:"
    echo "  1. Set up automatic SSL renewal: ./renew_ssl.sh"
    echo "  2. Configure firewall to allow only ports 22, 80, 443"
    echo "  3. Set up monitoring for certificate expiration"
    echo "  4. Regularly backup database and certificates"
    echo "  5. Test SSL configuration: https://www.ssllabs.com/ssltest/"
else
    print_status "🎉 Production deployment completed successfully!"
    print_warning "⚠️  SSL is not configured. Consider setting up SSL for production use."
fi

echo ""
print_info "For troubleshooting, see:"
echo "  - ./COMPLETE_API_DOCUMENTATION.md"
echo "  - ./SSL_SETUP_GUIDE.md"
echo "  - docker-compose logs"

echo ""
echo "$(date): Deployment completed"
