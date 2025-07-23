#!/bin/bash
set -e

# Deployment script for TradeRamp website to AWS Fargate

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
ECR_REPOSITORY="traderamp-production"
ECS_CLUSTER="traderamp-production-cluster"
ECS_SERVICE="traderamp-production"
CONTAINER_NAME="traderamp-production"

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

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
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

# Build Docker image
build_image() {
    print_status "Building Docker image..."
    
    if [ ! -f "Dockerfile" ]; then
        print_error "Dockerfile not found in current directory."
        exit 1
    fi
    
    docker build -t ${ECR_REPOSITORY}:latest .
    print_status "Docker image built successfully."
}

# Push to ECR
push_to_ecr() {
    print_status "Pushing image to ECR..."
    
    # Get ECR login
    aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.${AWS_REGION}.amazonaws.com
    
    # Get repository URI
    REPOSITORY_URI=$(aws ecr describe-repositories --repository-names ${ECR_REPOSITORY} --region ${AWS_REGION} --query 'repositories[0].repositoryUri' --output text)
    
    if [ -z "$REPOSITORY_URI" ]; then
        print_error "ECR repository ${ECR_REPOSITORY} not found."
        exit 1
    fi
    
    # Tag and push
    IMAGE_TAG=${IMAGE_TAG:-$(git rev-parse --short HEAD 2>/dev/null || echo "latest")}
    docker tag ${ECR_REPOSITORY}:latest ${REPOSITORY_URI}:${IMAGE_TAG}
    docker tag ${ECR_REPOSITORY}:latest ${REPOSITORY_URI}:latest
    
    docker push ${REPOSITORY_URI}:${IMAGE_TAG}
    docker push ${REPOSITORY_URI}:latest
    
    print_status "Image pushed to ECR successfully."
    echo "Image URI: ${REPOSITORY_URI}:${IMAGE_TAG}"
}

# Update ECS service
update_ecs_service() {
    print_status "Updating ECS service..."
    
    # Force new deployment
    aws ecs update-service \
        --cluster ${ECS_CLUSTER} \
        --service ${ECS_SERVICE} \
        --force-new-deployment \
        --region ${AWS_REGION} \
        --output text
    
    print_status "ECS service update initiated."
    
    # Wait for service to stabilize
    print_status "Waiting for service to stabilize..."
    aws ecs wait services-stable \
        --cluster ${ECS_CLUSTER} \
        --services ${ECS_SERVICE} \
        --region ${AWS_REGION}
    
    print_status "ECS service updated successfully."
}

# Get service status
get_service_status() {
    print_status "Getting service status..."
    
    aws ecs describe-services \
        --cluster ${ECS_CLUSTER} \
        --services ${ECS_SERVICE} \
        --region ${AWS_REGION} \
        --query 'services[0].{DesiredCount:desiredCount,RunningCount:runningCount,PendingCount:pendingCount,Status:status}' \
        --output table
}

# Main deployment flow
main() {
    print_status "Starting deployment process..."
    
    check_prerequisites
    build_image
    push_to_ecr
    update_ecs_service
    get_service_status
    
    print_status "Deployment completed successfully!"
    
    # Get ALB URL
    ALB_DNS=$(aws elbv2 describe-load-balancers --region ${AWS_REGION} --query "LoadBalancers[?contains(LoadBalancerName, 'traderamp')].DNSName" --output text)
    if [ ! -z "$ALB_DNS" ]; then
        echo ""
        print_status "Application URL: http://${ALB_DNS}"
    fi
}

# Run main function
main