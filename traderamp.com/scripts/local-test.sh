#!/bin/bash
set -e

# Local testing script for TradeRamp website

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# Build and run locally
print_status "Building Docker image..."
docker build -t traderamp-local .

print_status "Stopping any existing container..."
docker stop traderamp-test 2>/dev/null || true
docker rm traderamp-test 2>/dev/null || true

print_status "Starting container..."
docker run -d \
    --name traderamp-test \
    -p 8080:80 \
    traderamp-local

print_status "Container started successfully!"
echo ""
print_status "Website is available at: http://localhost:8080"
print_warning "Press Ctrl+C to stop the container"
echo ""

# Show logs
print_status "Container logs:"
docker logs -f traderamp-test