# TradeRamp Fargate Deployment Guide

## Overview

TradeRamp is deployed as a containerized static website on AWS Fargate using:
- **ECS Fargate** for serverless container hosting
- **Application Load Balancer** with SSL termination
- **ECR** for Docker image storage
- **Pulumi** for infrastructure as code
- **nginx** for serving static content

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. Docker installed and running
3. Pulumi CLI installed
4. Python 3.8+ with virtual environment

## Infrastructure Setup

### 1. Initial Pulumi Setup

```bash
cd pulumi
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Pulumi Stack

Select or create the production stack:
```bash
pulumi stack select production
# Or create new: pulumi stack new production
```

### 3. Deploy Infrastructure

```bash
pulumi up
```

This creates:
- VPC with public subnets
- Application Load Balancer with SSL certificate
- ECS Fargate cluster and service
- ECR repository
- Security groups
- Auto-scaling configuration

## Application Deployment

### 1. Build Docker Image

From the traderamp.com directory:
```bash
docker build -t traderamp:latest .
```

### 2. Deploy to AWS

Use the provided script:
```bash
./build-and-deploy.sh
```

Or manually:
```bash
# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=us-east-1

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Tag and push
docker tag traderamp:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/traderamp-production-ecr:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/traderamp-production-ecr:latest
```

### 3. Update ECS Service

Force a new deployment:
```bash
aws ecs update-service \
    --cluster traderamp-production-cluster \
    --service traderamp-production-service \
    --force-new-deployment \
    --region us-east-1
```

## Configuration

### Environment Variables

The Pulumi configuration supports these settings:

- `container_cpu`: CPU units (256, 512, 1024, 2048, 4096)
- `container_memory`: Memory in MB
- `desired_count`: Number of tasks to run
- `min_capacity`: Minimum tasks for auto-scaling
- `max_capacity`: Maximum tasks for auto-scaling
- `domain_name`: Your domain (e.g., traderamp.com)

### Updating Configuration

```bash
cd pulumi
pulumi config set container_cpu 512
pulumi config set desired_count 3
pulumi up
```

## Health Checks

The application includes:
- Docker health check at `/health`
- ALB health check configured for `/health` endpoint
- ECS service health check with 60s grace period

## Monitoring

View logs:
```bash
# View CloudWatch logs
aws logs tail /ecs/traderamp-production --follow

# View ECS service status
aws ecs describe-services \
    --cluster traderamp-production-cluster \
    --services traderamp-production-service
```

## SSL/TLS

- SSL certificates are automatically managed via AWS Certificate Manager
- The ALB handles SSL termination
- nginx serves content over HTTP within the VPC

## Scaling

Auto-scaling is configured based on:
- CPU utilization (target: 70%)
- Memory utilization (target: 70%)
- Min instances: 1
- Max instances: 4

Manual scaling:
```bash
aws ecs update-service \
    --cluster traderamp-production-cluster \
    --service traderamp-production-service \
    --desired-count 3
```

## Troubleshooting

### Container won't start
1. Check CloudWatch logs
2. Verify health check endpoint
3. Check nginx configuration

### 502 Bad Gateway
1. Verify ECS tasks are running
2. Check security group rules
3. Verify target group health

### Deployment not updating
1. Ensure new image was pushed to ECR
2. Force new deployment
3. Check service events in ECS console

## Cost Optimization

- Use Fargate Spot for non-production environments
- Adjust container size based on actual usage
- Enable CloudWatch Container Insights only when needed
- Set appropriate log retention periods

## Security

- Security groups restrict traffic appropriately
- Container runs as non-root nginx user
- Security headers configured in nginx
- Regular updates of base nginx:alpine image

## Backup and Recovery

- Infrastructure defined as code in Pulumi
- Docker images stored in ECR with lifecycle policies
- Static content in Git repository

## Clean Up

To destroy all resources:
```bash
cd pulumi
pulumi destroy
```

**Warning**: This will delete all infrastructure including the domain configuration.