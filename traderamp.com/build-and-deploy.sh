#!/bin/bash

# TradeRamp Docker Build and Deploy Script
# This script builds the Docker image and pushes it to ECR

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY="traderamp-dev"
IMAGE_TAG="${IMAGE_TAG:-latest}"

echo -e "${GREEN}TradeRamp Docker Build and Deploy${NC}"
echo "=================================="

# Check if AWS CLI is configured
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${RED}Error: AWS CLI not configured. Run 'aws configure' first.${NC}"
    exit 1
fi

echo "AWS Account ID: $AWS_ACCOUNT_ID"
echo "AWS Region: $AWS_REGION"
echo "ECR Repository: $ECR_REPOSITORY"
echo "Image Tag: $IMAGE_TAG"

# Get ECR login token
echo -e "\n${YELLOW}Logging in to ECR...${NC}"
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build Docker image
echo -e "\n${YELLOW}Building Docker image...${NC}"
docker build -t $ECR_REPOSITORY:$IMAGE_TAG .

# Tag image for ECR
echo -e "\n${YELLOW}Tagging image for ECR...${NC}"
docker tag $ECR_REPOSITORY:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG

# Push to ECR
echo -e "\n${YELLOW}Pushing image to ECR...${NC}"
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG

# Update ECS service (optional - requires ECS service name)
if [ "$UPDATE_SERVICE" = "true" ]; then
    echo -e "\n${YELLOW}Updating ECS service...${NC}"
    ECS_CLUSTER="traderamp-dev"
    ECS_SERVICE="traderamp-dev"
    
    aws ecs update-service \
        --cluster $ECS_CLUSTER \
        --service $ECS_SERVICE \
        --force-new-deployment \
        --region $AWS_REGION
    
    echo -e "${GREEN}ECS service update initiated${NC}"
fi

echo -e "\n${GREEN}Build and deploy complete!${NC}"
echo "Image pushed: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG"

# Instructions for deployment
echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. If not done already, run Pulumi to create/update infrastructure:"
echo "   cd pulumi && pulumi up"
echo "2. To force a new deployment:"
echo "   UPDATE_SERVICE=true ./build-and-deploy.sh"