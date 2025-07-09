#!/bin/bash

# SSL Testing and Validation Script for TravelTime Backend
# This script performs comprehensive SSL testing and validation

echo "=== TravelTime SSL Testing and Validation ==="
echo "$(date): Starting SSL tests"
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

# Test counter
TOTAL_TESTS=0
PASSED_TESTS=0

run_test() {
    local test_name="$1"
    local test_command="$2"
    local success_message="$3"
    local failure_message="$4"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo ""
    print_info "Test $TOTAL_TESTS: $test_name"
    
    if eval "$test_command" > /dev/null 2>&1; then
        print_status "$success_message"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        print_error "$failure_message"
        return 1
    fi
}

echo "=== Local Certificate Tests ==="

# Test 1: Check if certificate files exist
run_test "Certificate Files Exist" \
    "[ -f 'ssl/cert.pem' ] && [ -f 'ssl/key.pem' ]" \
    "Certificate files found" \
    "Certificate files missing (ssl/cert.pem or ssl/key.pem)"

if [ -f "ssl/cert.pem" ] && [ -f "ssl/key.pem" ]; then
    
    # Test 2: Validate certificate format
    run_test "Certificate Format Validation" \
        "openssl x509 -in ssl/cert.pem -text -noout" \
        "Certificate format is valid" \
        "Certificate format is invalid"
    
    # Test 3: Validate private key format
    run_test "Private Key Format Validation" \
        "openssl rsa -in ssl/key.pem -check -noout" \
        "Private key format is valid" \
        "Private key format is invalid"
    
    # Test 4: Check certificate and key match
    cert_modulus=$(openssl x509 -noout -modulus -in ssl/cert.pem 2>/dev/null | openssl md5 2>/dev/null)
    key_modulus=$(openssl rsa -noout -modulus -in ssl/key.pem 2>/dev/null | openssl md5 2>/dev/null)
    
    run_test "Certificate and Key Match" \
        "[ '$cert_modulus' = '$key_modulus' ]" \
        "Certificate and private key match" \
        "Certificate and private key do not match"
    
    # Test 5: Check certificate expiration
    run_test "Certificate Not Expired" \
        "openssl x509 -checkend 0 -noout -in ssl/cert.pem" \
        "Certificate is not expired" \
        "Certificate has expired"
    
    # Test 6: Check certificate expires in more than 7 days
    run_test "Certificate Valid for 7+ Days" \
        "openssl x509 -checkend $((7*24*60*60)) -noout -in ssl/cert.pem" \
        "Certificate is valid for more than 7 days" \
        "Certificate expires within 7 days"
    
    # Display certificate details
    echo ""
    print_info "Certificate Details:"
    echo "Subject: $(openssl x509 -in ssl/cert.pem -noout -subject 2>/dev/null | cut -d= -f2-)"
    echo "Issuer: $(openssl x509 -in ssl/cert.pem -noout -issuer 2>/dev/null | cut -d= -f2-)"
    echo "Valid from: $(openssl x509 -in ssl/cert.pem -noout -dates 2>/dev/null | grep notBefore | cut -d= -f2)"
    echo "Valid until: $(openssl x509 -in ssl/cert.pem -noout -dates 2>/dev/null | grep notAfter | cut -d= -f2)"
    
    # Check Subject Alternative Names
    san=$(openssl x509 -in ssl/cert.pem -text -noout 2>/dev/null | grep -A1 "Subject Alternative Name" | tail -1 | sed 's/^[[:space:]]*//')
    if [ -n "$san" ]; then
        echo "SAN: $san"
    fi
    
else
    print_warning "Skipping certificate validation tests - no certificates found"
fi

echo ""
echo "=== Service Tests ==="

# Test 7: Check if Docker containers are running
run_test "Docker Containers Running" \
    "docker-compose ps | grep -q 'Up'" \
    "Docker containers are running" \
    "Docker containers are not running"

# Test 8: API health check
run_test "API Health Check" \
    "curl -f -s http://localhost:8000/ping" \
    "API is responding to health checks" \
    "API is not responding"

# Test 9: Nginx configuration test
run_test "Nginx Configuration Valid" \
    "docker-compose exec -T nginx nginx -t" \
    "Nginx configuration is valid" \
    "Nginx configuration has errors"

echo ""
echo "=== Network Tests ==="

# Test 10: HTTP connection (local)
run_test "HTTP Connection (Local)" \
    "curl -s -I http://localhost | head -1 | grep -E '200|301|302'" \
    "HTTP connection successful" \
    "HTTP connection failed"

# Test 11: HTTPS connection (local, ignore cert validation)
if [ -f "ssl/cert.pem" ] && [ -f "ssl/key.pem" ]; then
    run_test "HTTPS Connection (Local)" \
        "curl -k -s -I https://localhost | head -1 | grep -E '200|301|302'" \
        "HTTPS connection successful" \
        "HTTPS connection failed"
fi

# Test 12: HTTP to HTTPS redirect
if [ -f "ssl/cert.pem" ] && [ -f "ssl/key.pem" ]; then
    run_test "HTTP to HTTPS Redirect" \
        "curl -s -I http://localhost | grep -E 'Location:.*https'" \
        "HTTP to HTTPS redirect is working" \
        "HTTP to HTTPS redirect not configured"
fi

echo ""
echo "=== External Domain Tests ==="

# Test 13: DNS resolution
run_test "DNS Resolution for tt.owohappy.com" \
    "nslookup tt.owohappy.com" \
    "DNS resolution successful" \
    "DNS resolution failed"

# Test 14: External HTTP connection
run_test "External HTTP Connection" \
    "curl -s -I --connect-timeout 10 http://tt.owohappy.com | head -1 | grep -E '200|301|302'" \
    "External HTTP connection successful" \
    "External HTTP connection failed"

# Test 15: External HTTPS connection
if [ -f "ssl/cert.pem" ] && [ -f "ssl/key.pem" ]; then
    run_test "External HTTPS Connection" \
        "curl -s -I --connect-timeout 10 https://tt.owohappy.com | head -1 | grep -E '200|301|302'" \
        "External HTTPS connection successful" \
        "External HTTPS connection failed"
fi

echo ""
echo "=== API Endpoint Tests ==="

# Test 16: Ping endpoint
run_test "Ping Endpoint" \
    "curl -s http://localhost:8000/ping | grep -q 'pong'" \
    "Ping endpoint working" \
    "Ping endpoint failed"

# Test 17: Health endpoint
run_test "Health Endpoint" \
    "curl -s http://localhost:8000/health | grep -q 'status'" \
    "Health endpoint working" \
    "Health endpoint failed"

echo ""
echo "=== Security Headers Test ==="

if [ -f "ssl/cert.pem" ] && [ -f "ssl/key.pem" ]; then
    # Test 18: HSTS header
    run_test "HSTS Header Present" \
        "curl -k -s -I https://localhost | grep -i 'strict-transport-security'" \
        "HSTS header is present" \
        "HSTS header is missing"
    
    # Test 19: Security headers
    run_test "Security Headers Present" \
        "curl -k -s -I https://localhost | grep -E '(X-Frame-Options|X-Content-Type-Options|X-XSS-Protection)'" \
        "Security headers are present" \
        "Some security headers are missing"
fi

echo ""
echo "=== Performance Tests ==="

# Test 20: Response time
response_time=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:8000/ping 2>/dev/null)
if [ -n "$response_time" ]; then
    if (( $(echo "$response_time < 1.0" | bc -l) )); then
        run_test "API Response Time" \
            "true" \
            "API response time is good (${response_time}s)" \
            ""
    else
        run_test "API Response Time" \
            "false" \
            "" \
            "API response time is slow (${response_time}s)"
    fi
else
    run_test "API Response Time" \
        "false" \
        "" \
        "Unable to measure API response time"
fi

echo ""
echo "=== SSL Quality Test (External) ==="

if [ -f "ssl/cert.pem" ] && [ -f "ssl/key.pem" ]; then
    print_info "For comprehensive SSL analysis, visit:"
    echo "  https://www.ssllabs.com/ssltest/analyze.html?d=tt.owohappy.com"
    echo ""
    print_info "Expected grade: A or A+ for properly configured Let's Encrypt certificate"
fi

echo ""
echo "=== Test Summary ==="
echo ""

success_rate=$(( (PASSED_TESTS * 100) / TOTAL_TESTS ))

echo "Tests Passed: $PASSED_TESTS / $TOTAL_TESTS"
echo "Success Rate: $success_rate%"

if [ $success_rate -ge 90 ]; then
    print_status "🎉 Excellent! SSL configuration is working properly."
elif [ $success_rate -ge 75 ]; then
    print_warning "⚠️  Good, but some issues detected. Review failed tests above."
elif [ $success_rate -ge 50 ]; then
    print_warning "⚠️  Multiple issues detected. SSL may not be working correctly."
else
    print_error "❌ Significant issues detected. SSL setup needs attention."
fi

echo ""
echo "=== Troubleshooting Guide ==="
echo ""

if [ $PASSED_TESTS -lt $TOTAL_TESTS ]; then
    echo "Common issues and solutions:"
    echo ""
    
    if [ ! -f "ssl/cert.pem" ] || [ ! -f "ssl/key.pem" ]; then
        echo "• Missing certificates: Run ./setup_ssl.sh"
    fi
    
    echo "• Container issues: docker-compose down && docker-compose up -d"
    echo "• Certificate issues: Check ./SSL_SETUP_GUIDE.md"
    echo "• Network issues: Check firewall settings (ports 80, 443)"
    echo "• DNS issues: Verify domain points to correct server IP"
    echo "• External access: Check if server is behind NAT/firewall"
    echo ""
    echo "Useful debugging commands:"
    echo "  docker-compose logs nginx"
    echo "  docker-compose logs api"
    echo "  openssl s_client -connect tt.owohappy.com:443"
    echo "  curl -v https://tt.owohappy.com/ping"
fi

echo ""
echo "$(date): SSL testing completed"
