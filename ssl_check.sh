#!/bin/bash

# Quick SSL Setup Verification Script
# This script provides a fast check of SSL configuration

echo "=== TravelTime SSL Quick Check ==="
echo ""

# Function to print colored output
print_status() {
    echo -e "\033[0;32m✅ $1\033[0m"
}

print_error() {
    echo -e "\033[0;31m❌ $1\033[0m"
}

print_info() {
    echo -e "\033[0;34mℹ️  $1\033[0m"
}

# Check certificate files
if [ -f "ssl/cert.pem" ] && [ -f "ssl/key.pem" ]; then
    print_status "SSL certificate files found"
    
    # Quick certificate validation
    if openssl x509 -in ssl/cert.pem -noout -subject > /dev/null 2>&1; then
        print_status "Certificate is valid"
        
        # Show expiration
        expiry=$(openssl x509 -in ssl/cert.pem -noout -dates | grep notAfter | cut -d= -f2)
        print_info "Certificate expires: $expiry"
        
        # Check if expires soon
        if openssl x509 -checkend $((7*24*60*60)) -noout -in ssl/cert.pem; then
            print_status "Certificate valid for 7+ days"
        else
            print_error "Certificate expires within 7 days!"
        fi
    else
        print_error "Certificate file is invalid"
    fi
else
    print_error "SSL certificate files not found"
    echo ""
    print_info "To set up SSL certificates, run: ./setup_ssl.sh"
fi

echo ""

# Check if Docker containers are running
if docker-compose ps 2>/dev/null | grep -q "Up"; then
    print_status "Docker containers are running"
    
    # Quick API test
    if curl -s http://localhost:8000/ping | grep -q "pong"; then
        print_status "API is responding"
    else
        print_error "API is not responding"
    fi
    
    # Quick HTTPS test
    if [ -f "ssl/cert.pem" ]; then
        if curl -k -s https://localhost/ping | grep -q "pong"; then
            print_status "HTTPS is working"
        else
            print_error "HTTPS is not working"
        fi
    fi
    
else
    print_error "Docker containers are not running"
    echo ""
    print_info "To start services, run: docker-compose up -d"
fi

echo ""

# Show useful commands
print_info "Useful commands:"
echo "  Full SSL test:       ./test_ssl.sh"
echo "  Complete deployment: ./deploy_production.sh"
echo "  SSL setup:           ./setup_ssl.sh"
echo "  View logs:           docker-compose logs -f"
echo "  Service status:      docker-compose ps"

echo ""
echo "=== Quick Check Complete ==="
