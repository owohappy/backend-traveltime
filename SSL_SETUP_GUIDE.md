# SSL Configuration and Certificate Management

This directory contains SSL certificates and related configuration for the TravelTime backend production deployment.

## Files

### SSL Certificates
- `cert.pem` - The SSL certificate (full certificate chain)
- `key.pem` - The private key for the certificate

### Security Notes
- These files contain sensitive cryptographic material
- Never commit certificates to version control
- Ensure proper file permissions (readable by nginx, not world-readable for private key)
- Backup certificates before renewal

## Certificate Types

### 1. Let's Encrypt (Recommended for Production)
- Free, automated SSL certificates
- Automatically trusted by all major browsers
- 90-day validity period with automatic renewal
- Use `../setup_ssl.sh` to obtain certificates

### 2. Self-Signed (Testing Only)
- Free but shows security warnings in browsers
- Suitable for development and testing
- Not recommended for production use

### 3. Commercial Certificates
- Purchased from Certificate Authorities
- Longer validity periods (1+ years)
- May include warranty/insurance

## Setup Instructions

### Initial Setup
```bash
# Run the SSL setup script
./setup_ssl.sh
```

### Let's Encrypt Setup
```bash
# Prerequisites:
# 1. Domain tt.owohappy.com must point to this server
# 2. Ports 80 and 443 must be accessible
# 3. No other web server running on port 80

# The setup script will:
# 1. Install certbot if needed
# 2. Obtain certificate using webroot method
# 3. Copy certificates to ssl/ directory
# 4. Set proper permissions
```

### Manual Certificate Installation
```bash
# If you have existing certificates:
# 1. Copy your certificate chain to ssl/cert.pem
# 2. Copy your private key to ssl/key.pem
# 3. Set proper permissions:
chmod 644 ssl/cert.pem
chmod 600 ssl/key.pem
```

## Certificate Renewal

### Automatic Renewal (Recommended)
```bash
# Add to crontab for automatic renewal:
# This checks daily and renews if certificate expires within 30 days
0 2 * * * /path/to/backend-traveltime/renew_ssl.sh >> /var/log/ssl-renewal.log 2>&1
```

### Manual Renewal
```bash
# For Let's Encrypt certificates:
./renew_ssl.sh

# Or manually:
sudo certbot renew
sudo cp /etc/letsencrypt/live/tt.owohappy.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/tt.owohappy.com/privkey.pem ssl/key.pem
docker-compose exec nginx nginx -s reload
```

## Testing SSL Configuration

### Basic SSL Test
```bash
# Test SSL connection
curl -I https://tt.owohappy.com

# Test with verbose output
curl -v https://tt.owohappy.com/ping
```

### SSL Certificate Details
```bash
# View certificate information
openssl x509 -in ssl/cert.pem -text -noout

# Check certificate expiration
openssl x509 -in ssl/cert.pem -noout -dates

# Verify certificate and key match
openssl x509 -noout -modulus -in ssl/cert.pem | openssl md5
openssl rsa -noout -modulus -in ssl/key.pem | openssl md5
# The MD5 hashes should match
```

### Online SSL Testing
- SSL Labs Test: https://www.ssllabs.com/ssltest/
- Enter domain: tt.owohappy.com
- Wait for comprehensive SSL analysis

## Troubleshooting

### Common Issues

#### Certificate Not Found
```bash
# Error: nginx: [emerg] cannot load certificate "/etc/nginx/ssl/cert.pem"
# Solution: Ensure certificates exist and have proper permissions
ls -la ssl/
chmod 644 ssl/cert.pem
chmod 600 ssl/key.pem
```

#### Certificate/Key Mismatch
```bash
# Error: nginx: [emerg] SSL_CTX_use_PrivateKey_file() failed
# Solution: Verify certificate and key match
openssl x509 -noout -modulus -in ssl/cert.pem | openssl md5
openssl rsa -noout -modulus -in ssl/key.pem | openssl md5
```

#### Let's Encrypt Rate Limits
```bash
# Error: too many certificates already issued
# Solution: Wait or use staging environment for testing
# Staging: certbot --staging
```

#### Domain Validation Failed
```bash
# Error: Challenge failed for domain tt.owohappy.com
# Solutions:
# 1. Ensure domain points to correct server IP
# 2. Check firewall allows ports 80/443
# 3. Stop other web servers using port 80
# 4. Verify webroot path is accessible
```

### Log Files
```bash
# Nginx SSL errors
docker-compose logs nginx | grep -i ssl

# Let's Encrypt logs
sudo tail -f /var/log/letsencrypt/letsencrypt.log

# SSL renewal logs
tail -f /var/log/ssl-renewal.log
```

### Emergency Certificate Reset
```bash
# If certificates are corrupted or compromised:
# 1. Stop services
docker-compose down

# 2. Backup current certificates
mv ssl ssl_backup_$(date +%Y%m%d_%H%M%S)

# 3. Create new ssl directory
mkdir ssl

# 4. Run setup script again
./setup_ssl.sh

# 5. Start services
docker-compose up -d
```

## Security Best Practices

1. **File Permissions**: Private keys should be readable only by nginx (600)
2. **Backup Strategy**: Regular backups of certificates before renewal
3. **Monitoring**: Monitor certificate expiration dates
4. **Renewal**: Automate certificate renewal with cron jobs
5. **Testing**: Regular SSL configuration testing
6. **Logs**: Monitor SSL-related logs for errors

## Production Checklist

- [ ] SSL certificates installed and valid
- [ ] Certificate and private key match
- [ ] Proper file permissions set
- [ ] Nginx configuration tested
- [ ] HTTPS redirect working (HTTP → HTTPS)
- [ ] SSL Labs test shows A+ rating
- [ ] Automatic renewal configured
- [ ] Monitoring alerts for certificate expiration
- [ ] Backup procedures in place
