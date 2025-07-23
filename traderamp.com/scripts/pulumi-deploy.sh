#!/bin/bash
set -e

# Pulumi deployment script for TradeRamp

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PULUMI_DIR="pulumi"
STACK="${PULUMI_STACK:-production}"
AWS_REGION="${AWS_REGION:-us-east-1}"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

print_info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Pulumi CLI
    if ! command -v pulumi &> /dev/null; then
        print_error "Pulumi CLI is not installed. Please install it first."
        print_info "Visit: https://www.pulumi.com/docs/get-started/install/"
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install it first."
        exit 1
    fi
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials are not configured. Please run 'aws configure'."
        exit 1
    fi
    
    print_status "Prerequisites check passed."
}

# Setup Pulumi environment
setup_pulumi() {
    print_status "Setting up Pulumi environment..."
    
    cd "$PULUMI_DIR"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_info "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    print_info "Installing Python dependencies..."
    pip install -r requirements.txt
    
    # Login to Pulumi (using local backend by default)
    if [ -z "$PULUMI_ACCESS_TOKEN" ]; then
        print_info "Using local Pulumi backend..."
        pulumi login --local
    else
        print_info "Using Pulumi service backend..."
        pulumi login
    fi
    
    # Select or create stack
    if pulumi stack ls 2>/dev/null | grep -q "$STACK"; then
        print_info "Selecting stack: $STACK"
        pulumi stack select "$STACK"
    else
        print_info "Creating new stack: $STACK"
        pulumi stack init "$STACK"
    fi
}

# Build and push Docker image
build_and_push_image() {
    print_status "Building and pushing Docker image..."
    
    cd ..  # Back to project root
    
    # Get ECR repository URL from Pulumi
    ECR_URL=$(cd "$PULUMI_DIR" && pulumi stack output ecr_repository_url 2>/dev/null || echo "")
    
    if [ -z "$ECR_URL" ]; then
        print_warning "ECR repository not found. It will be created during deployment."
        return
    fi
    
    # Login to ECR
    print_info "Logging in to ECR..."
    aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "${ECR_URL%/*}"
    
    # Build image
    print_info "Building Docker image..."
    docker build -t traderamp:latest .
    
    # Tag image
    IMAGE_TAG="${IMAGE_TAG:-latest}"
    docker tag traderamp:latest "$ECR_URL:$IMAGE_TAG"
    docker tag traderamp:latest "$ECR_URL:latest"
    
    # Push image
    print_info "Pushing image to ECR..."
    docker push "$ECR_URL:$IMAGE_TAG"
    docker push "$ECR_URL:latest"
    
    print_status "Docker image pushed successfully."
}

# Deploy infrastructure
deploy_infrastructure() {
    print_status "Deploying infrastructure with Pulumi..."
    
    cd "$PULUMI_DIR"
    
    # Preview changes
    print_info "Previewing changes..."
    pulumi preview
    
    # Confirm deployment
    read -p "Do you want to proceed with deployment? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Deployment cancelled."
        exit 0
    fi
    
    # Deploy
    print_info "Deploying infrastructure..."
    pulumi up --yes
    
    print_status "Infrastructure deployed successfully."
}

# Update ECS service
update_ecs_service() {
    print_status "Updating ECS service..."
    
    cd "$PULUMI_DIR"
    
    # Get service details from Pulumi
    CLUSTER_NAME=$(pulumi stack output ecs_cluster_name 2>/dev/null || echo "")
    SERVICE_NAME=$(pulumi stack output ecs_service_name 2>/dev/null || echo "")
    
    if [ -z "$CLUSTER_NAME" ] || [ -z "$SERVICE_NAME" ]; then
        print_warning "ECS service not found. Skipping service update."
        return
    fi
    
    # Force new deployment
    print_info "Forcing new deployment..."
    aws ecs update-service \
        --cluster "$CLUSTER_NAME" \
        --service "$SERVICE_NAME" \
        --force-new-deployment \
        --region "$AWS_REGION" \
        --output text
    
    print_info "Waiting for service to stabilize..."
    aws ecs wait services-stable \
        --cluster "$CLUSTER_NAME" \
        --services "$SERVICE_NAME" \
        --region "$AWS_REGION"
    
    print_status "ECS service updated successfully."
}

# Show deployment info
show_deployment_info() {
    print_status "Deployment Information:"
    
    cd "$PULUMI_DIR"
    
    echo ""
    pulumi stack output
    echo ""
    
    # Get website URL
    WEBSITE_URL=$(pulumi stack output website_url 2>/dev/null || echo "")
    if [ ! -z "$WEBSITE_URL" ]; then
        print_status "Website URL: $WEBSITE_URL"
    fi
}

# Main deployment flow
main() {
    print_status "Starting Pulumi deployment for TradeRamp..."
    print_info "Stack: $STACK"
    print_info "Region: $AWS_REGION"
    echo ""
    
    check_prerequisites
    setup_pulumi
    
    # First deployment - just infrastructure
    if [ "$1" == "--infra-only" ]; then
        deploy_infrastructure
        show_deployment_info
        exit 0
    fi
    
    # Full deployment
    deploy_infrastructure
    build_and_push_image
    update_ecs_service
    show_deployment_info
    
    print_status "Deployment completed successfully!"
}

# Handle arguments
case "$1" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --infra-only    Deploy only infrastructure (no Docker build)"
        echo "  --help, -h      Show this help message"
        echo ""
        echo "Environment variables:"
        echo "  PULUMI_STACK    Pulumi stack to use (default: production)"
        echo "  AWS_REGION      AWS region (default: us-east-1)"
        echo "  IMAGE_TAG       Docker image tag (default: latest)"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac