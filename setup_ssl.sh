#!/bin/bash

# SSL Setup Script for TravelTime Backend
# This script helps set up SSL certificates for production deployment

echo "=== TravelTime Backend SSL Setup ==="
echo ""

# Create SSL directory if it doesn't exist
mkdir -p ssl

# Check if certificates already exist
if [ -f "ssl/cert.pem" ] && [ -f "ssl/key.pem" ]; then
    echo "✅ SSL certificates already exist in ssl/ directory"
    echo ""
    echo "Certificate details:"
    openssl x509 -in ssl/cert.pem -text -noout | grep -E "(Subject|Issuer|Not Before|Not After)" || echo "Unable to read certificate details"
    echo ""
else
    echo "🔧 SSL certificates not found. Let's set them up..."
    echo ""
    echo "Choose your SSL certificate option:"
    echo "1) Let's Encrypt (Recommended for production)"
    echo "2) Self-signed certificate (For testing only)"
    echo "3) Use existing certificates (I'll provide the files)"
    echo ""
    read -p "Enter your choice (1-3): " choice

    case $choice in
        1)
            echo ""
            echo "=== Let's Encrypt Setup ==="
            echo ""
            echo "For Let's Encrypt certificates, you need to:"
            echo "1. Ensure your domain (tt.owohappy.com) points to this server"
            echo "2. Have ports 80 and 443 open and accessible"
            echo "3. Install certbot if not already installed"
            echo ""
            
            # Check if certbot is installed
            if ! command -v certbot &> /dev/null; then
                echo "Installing certbot..."
                if command -v apt-get &> /dev/null; then
                    sudo apt-get update
                    sudo apt-get install -y certbot
                elif command -v yum &> /dev/null; then
                    sudo yum install -y certbot
                elif command -v dnf &> /dev/null; then
                    sudo dnf install -y certbot
                else
                    echo "❌ Unable to install certbot automatically. Please install it manually."
                    exit 1
                fi
            fi
            
            echo ""
            echo "Running certbot to obtain certificate..."
            echo "This will use the webroot method with nginx serving the challenge."
            echo ""
            
            # Create webroot directory for ACME challenge
            sudo mkdir -p /var/www/certbot
            
            # Obtain certificate
            sudo certbot certonly \
                --webroot \
                --webroot-path=/var/www/certbot \
                --email admin@owohappy.com \
                --agree-tos \
                --no-eff-email \
                -d tt.owohappy.com
            
            if [ $? -eq 0 ]; then
                echo "✅ Let's Encrypt certificate obtained successfully!"
                echo ""
                echo "Copying certificates to ssl/ directory..."
                sudo cp /etc/letsencrypt/live/tt.owohappy.com/fullchain.pem ssl/cert.pem
                sudo cp /etc/letsencrypt/live/tt.owohappy.com/privkey.pem ssl/key.pem
                sudo chown $(whoami):$(whoami) ssl/cert.pem ssl/key.pem
                echo "✅ Certificates copied successfully!"
            else
                echo "❌ Failed to obtain Let's Encrypt certificate."
                echo "Please check that:"
                echo "- Domain tt.owohappy.com points to this server"
                echo "- Ports 80 and 443 are accessible"
                echo "- No other web server is running on port 80"
                exit 1
            fi
            ;;
        2)
            echo ""
            echo "=== Creating Self-Signed Certificate ==="
            echo "⚠️  This is for testing only and will show security warnings in browsers"
            echo ""
            
            openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                -keyout ssl/key.pem \
                -out ssl/cert.pem \
                -subj "/C=US/ST=State/L=City/O=Organization/CN=tt.owohappy.com"
            
            if [ $? -eq 0 ]; then
                echo "✅ Self-signed certificate created successfully!"
                echo "⚠️  Remember: This is for testing only and will show security warnings"
            else
                echo "❌ Failed to create self-signed certificate"
                exit 1
            fi
            ;;
        3)
            echo ""
            echo "=== Using Existing Certificates ==="
            echo ""
            echo "Please place your certificate files in the ssl/ directory:"
            echo "- Certificate: ssl/cert.pem (full certificate chain)"
            echo "- Private key: ssl/key.pem"
            echo ""
            echo "Make sure the files have proper permissions (readable by nginx)"
            echo ""
            read -p "Press Enter when you've placed the certificate files..."
            
            if [ -f "ssl/cert.pem" ] && [ -f "ssl/key.pem" ]; then
                echo "✅ Certificate files found!"
            else
                echo "❌ Certificate files not found. Please ensure both cert.pem and key.pem exist in ssl/"
                exit 1
            fi
            ;;
        *)
            echo "❌ Invalid choice. Exiting."
            exit 1
            ;;
    esac
fi

echo ""
echo "=== Validating SSL Configuration ==="
echo ""

# Validate certificate and key
if openssl x509 -in ssl/cert.pem -text -noout > /dev/null 2>&1; then
    echo "✅ Certificate file is valid"
else
    echo "❌ Certificate file is invalid or corrupted"
    exit 1
fi

if openssl rsa -in ssl/key.pem -check -noout > /dev/null 2>&1; then
    echo "✅ Private key file is valid"
else
    echo "❌ Private key file is invalid or corrupted"
    exit 1
fi

# Check if certificate and key match
cert_modulus=$(openssl x509 -noout -modulus -in ssl/cert.pem | openssl md5)
key_modulus=$(openssl rsa -noout -modulus -in ssl/key.pem | openssl md5)

if [ "$cert_modulus" = "$key_modulus" ]; then
    echo "✅ Certificate and private key match"
else
    echo "❌ Certificate and private key do not match"
    exit 1
fi

echo ""
echo "=== SSL Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Start the services: docker-compose up -d"
echo "2. Check nginx logs: docker-compose logs nginx"
echo "3. Test SSL: curl -I https://tt.owohappy.com"
echo ""
echo "Certificate details:"
openssl x509 -in ssl/cert.pem -text -noout | grep -E "(Subject|Issuer|Not Before|Not After)"
echo ""
echo "🎉 SSL is ready for production!"
