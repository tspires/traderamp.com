# TradeRamp AWS Fargate Deployment Guide

This guide explains how to deploy the TradeRamp website to AWS using Fargate.

## Architecture Overview

The deployment uses the following AWS services:
- **Amazon ECS with Fargate**: Serverless container hosting
- **Application Load Balancer (ALB)**: Distributes traffic across containers
- **Amazon ECR**: Container registry for Docker images
- **Route 53**: DNS management (optional)
- **ACM**: SSL certificate management
- **CloudWatch**: Logging and monitoring
- **Auto Scaling**: Automatic scaling based on CPU/memory usage

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured
3. **Docker** installed locally
4. **Pulumi** (v3.0+) for infrastructure deployment
5. **Python 3.8+** for Pulumi Python SDK
6. **Domain name** (optional, for custom domain)

## Initial Setup

### 1. Configure AWS Credentials

```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and preferred region
```

### 2. Install Pulumi

```bash
# macOS
brew install pulumi

# Or using the installation script
curl -fsSL https://get.pulumi.com | sh
```

### 3. Deploy Infrastructure with Pulumi

```bash
cd pulumi

# Create a new Pulumi stack
pulumi stack init production

# Set AWS region
pulumi config set aws:region us-east-1

# Set configuration values
pulumi config set container_cpu 256
pulumi config set container_memory 512
pulumi config set desired_count 2
pulumi config set min_capacity 1
pulumi config set max_capacity 4
pulumi config set domain_name traderamp.com

# Deploy the infrastructure
pulumi up
```

### 4. Update GitHub Secrets

Add the following secrets to your GitHub repository:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `PULUMI_ACCESS_TOKEN`

## Deployment Options

### Option 1: Automated Deployment via GitHub Actions

Simply push to the `main` or `master` branch:

```bash
git add .
git commit -m "Update website content"
git push origin main
```

The GitHub Actions workflow will automatically:
1. Build the Docker image
2. Push to ECR
3. Update the ECS service

### Option 2: Manual Deployment

Use the provided deployment script:

```bash
cd /path/to/traderamp.com
./scripts/deploy.sh
```

### Option 3: Local Testing

Test the containerized website locally:

```bash
./scripts/local-test.sh
# Website will be available at http://localhost:8080
```

## Configuration

### Pulumi Configuration

View current configuration:

```bash
pulumi config
```

Update configuration values:

```bash
pulumi config set project_name traderamp
pulumi config set environment production
pulumi config set domain_name traderamp.com

# Container sizing
pulumi config set container_cpu 256      # 0.25 vCPU
pulumi config set container_memory 512   # 512 MB

# Auto-scaling
pulumi config set desired_count 2
pulumi config set min_capacity 1
pulumi config set max_capacity 4
```

### Environment-Specific Deployments

For staging/development environments, create separate stacks:

```bash
# Create staging stack
pulumi stack init staging

# Switch between stacks
pulumi stack select staging
pulumi up

# Switch back to production
pulumi stack select production
```

## Custom Domain Setup

### 1. Route 53 Hosted Zone

Ensure your domain is using Route 53 name servers:
1. Create a hosted zone in Route 53
2. Update your domain registrar with Route 53 name servers

### 2. SSL Certificate

The Pulumi configuration automatically:
- Creates an ACM certificate for your domain
- Validates it via DNS
- Attaches it to the load balancer

### 3. DNS Records

The infrastructure automatically creates:
- A record for `traderamp.com`
- A record for `www.traderamp.com`

## Monitoring and Troubleshooting

### View Logs

```bash
# View recent logs
aws logs tail /ecs/traderamp-production --follow

# View specific task logs
aws ecs describe-tasks --cluster traderamp-production-cluster --tasks <task-arn>
```

### Check Service Status

```bash
# Service status
aws ecs describe-services --cluster traderamp-production-cluster --services traderamp-production

# Running tasks
aws ecs list-tasks --cluster traderamp-production-cluster --service traderamp-production
```

### View Pulumi Stack Outputs

```bash
# View all stack outputs
pulumi stack output

# View specific output
pulumi stack output alb_url
```

### Common Issues

1. **Container fails health checks**
   - Check CloudWatch logs
   - Ensure `/health` endpoint returns 200
   - Verify security group rules

2. **Service not reaching desired count**
   - Check task definition CPU/memory settings
   - Review subnet capacity
   - Check for image pull errors

3. **Website not accessible**
   - Verify ALB security group allows traffic on ports 80/443
   - Check target group health
   - Ensure DNS propagation is complete

## Scaling

### Manual Scaling

```bash
# Update desired count
aws ecs update-service \
  --cluster traderamp-production-cluster \
  --service traderamp-production \
  --desired-count 3
```

### Auto Scaling Configuration

The service automatically scales based on:
- CPU utilization > 70%
- Memory utilization > 70%

Modify scaling thresholds:

```bash
pulumi config set scale_up_cpu_threshold 70
pulumi config set scale_up_memory_threshold 70
pulumi up
```

## Cost Optimization

1. **Right-size containers**: Start with minimal CPU/memory and increase as needed
2. **Use Fargate Spot**: For non-production environments, enable Spot capacity
3. **Set appropriate auto-scaling limits**: Prevent runaway costs
4. **Enable CloudWatch Logs retention**: Set appropriate retention periods

## Security Best Practices

1. **Use least-privilege IAM roles**
2. **Enable VPC Flow Logs**
3. **Keep containers updated**: Rebuild and deploy regularly
4. **Use secrets manager**: For API keys and sensitive data
5. **Enable GuardDuty**: For threat detection

## Cleanup

To remove all resources:

```bash
cd pulumi
pulumi destroy
```

⚠️ **Warning**: This will delete all infrastructure including:
- ECS cluster and services
- Load balancer
- VPC and networking
- ECR repository (and images)

## Stack Management

### List all stacks
```bash
pulumi stack ls
```

### Export stack state
```bash
pulumi stack export > stack-backup.json
```

### Import stack state
```bash
pulumi stack import < stack-backup.json
```

## Support

For issues or questions:
1. Check CloudWatch logs
2. Review ECS service events
3. Verify Pulumi state is consistent (`pulumi refresh`)
4. Check AWS service health dashboard
5. Review Pulumi console for detailed resource information