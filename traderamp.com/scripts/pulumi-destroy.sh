#!/bin/bash
set -e

# Pulumi destroy script for TradeRamp

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PULUMI_DIR="pulumi"
STACK="${PULUMI_STACK:-production}"

print_status() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Main function
main() {
    print_warning "This will destroy all infrastructure for stack: $STACK"
    print_warning "This action cannot be undone!"
    echo ""
    
    read -p "Are you sure you want to destroy all resources? Type 'yes' to confirm: " -r
    echo
    if [[ ! $REPLY == "yes" ]]; then
        print_status "Destroy operation cancelled."
        exit 0
    fi
    
    cd "$PULUMI_DIR"
    
    # Activate virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Select stack
    pulumi stack select "$STACK"
    
    # Show what will be destroyed
    print_status "Resources to be destroyed:"
    pulumi preview --destroy
    
    # Final confirmation
    read -p "Proceed with destruction? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Destroy operation cancelled."
        exit 0
    fi
    
    # Destroy
    print_status "Destroying infrastructure..."
    pulumi destroy --yes
    
    print_status "Infrastructure destroyed successfully."
    
    # Optional: Remove the stack
    read -p "Do you also want to remove the Pulumi stack? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pulumi stack rm "$STACK" --yes
        print_status "Stack removed."
    fi
}

main