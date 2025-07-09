#!/bin/bash

# SSL Certificate Renewal Script for Let's Encrypt
# Add this to cron to automatically renew certificates

echo "=== TravelTime SSL Certificate Renewal ==="
echo "$(date): Starting certificate renewal check"

# Check if certificate expires within 30 days
if openssl x509 -checkend $((30*24*60*60)) -noout -in ssl/cert.pem; then
    echo "$(date): Certificate is still valid for more than 30 days. No renewal needed."
    exit 0
else
    echo "$(date): Certificate expires within 30 days. Attempting renewal..."
fi

# Backup current certificates
echo "$(date): Backing up current certificates..."
mkdir -p ssl/backup/$(date +%Y%m%d_%H%M%S)
cp ssl/cert.pem ssl/backup/$(date +%Y%m%d_%H%M%S)/cert.pem.bak
cp ssl/key.pem ssl/backup/$(date +%Y%m%d_%H%M%S)/key.pem.bak

# Renew certificate
echo "$(date): Attempting to renew Let's Encrypt certificate..."
sudo certbot renew --webroot --webroot-path=/var/www/certbot

if [ $? -eq 0 ]; then
    echo "$(date): Certificate renewed successfully!"
    
    # Copy new certificates
    echo "$(date): Copying new certificates..."
    sudo cp /etc/letsencrypt/live/tt.owohappy.com/fullchain.pem ssl/cert.pem
    sudo cp /etc/letsencrypt/live/tt.owohappy.com/privkey.pem ssl/key.pem
    sudo chown $(whoami):$(whoami) ssl/cert.pem ssl/key.pem
    
    # Reload nginx
    echo "$(date): Reloading nginx..."
    docker-compose exec nginx nginx -s reload
    
    if [ $? -eq 0 ]; then
        echo "$(date): Nginx reloaded successfully!"
        echo "$(date): SSL certificate renewal completed successfully!"
    else
        echo "$(date): Failed to reload nginx. Manual intervention required."
        exit 1
    fi
else
    echo "$(date): Certificate renewal failed. Check logs for details."
    exit 1
fi

echo "$(date): Certificate renewal process completed."
