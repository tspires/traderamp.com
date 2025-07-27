# TradeRamp AWS Fargate Deployment with Pulumi

This guide explains how to deploy the TradeRamp website to AWS using Pulumi (Infrastructure as Code in Python).

## Why Pulumi?

- **Python-native**: Write infrastructure code in Python, no need to learn HCL
- **Type safety**: Full IDE support with autocomplete and type checking
- **Real programming**: Use loops, conditionals, functions, and classes
- **Better secrets management**: Built-in encryption for sensitive values
- **Easier testing**: Unit test your infrastructure code

## Architecture Overview

The infrastructure is implemented in Python using Pulumi:
- Amazon ECS with Fargate
- Application Load Balancer (ALB)
- Amazon ECR for container registry
- Route 53 for DNS
- ACM for SSL certificates
- CloudWatch for logging
- Auto Scaling based on CPU/memory

## Prerequisites

1. **Python 3.8+** installed
2. **Pulumi CLI** installed
3. **AWS CLI** configured with credentials
4. **Docker** for building images
5. **Domain name** in Route 53 (optional)

## Quick Start

### 1. Install Pulumi

```bash
# macOS
brew install pulumi

# Linux/Windows
curl -fsSL https://get.pulumi.com | sh
```

### 2. Setup Python Environment

```bash
cd pulumi
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Pulumi Backend

```bash
# Option 1: Use Pulumi Service (recommended for teams)
pulumi login

# Option 2: Use local backend
pulumi login --local
```

### 4. Deploy Infrastructure

```bash
# First time setup
cd ..
./scripts/pulumi-deploy.sh --infra-only

# Full deployment (infrastructure + application)
./scripts/pulumi-deploy.sh
```

## Configuration

### Stack Configuration

Pulumi uses stacks for different environments. Configure with:

```bash
cd pulumi

# Set configuration values
pulumi config set aws:region us-east-1
pulumi config set traderamp:domain traderamp.com
pulumi config set traderamp:container_cpu 256
pulumi config set traderamp:container_memory 512
```

Or use pre-configured stack files:
- `Pulumi.production.yaml` - Production settings
- `Pulumi.staging.yaml` - Staging settings

### Environment-Specific Deployments

```bash
# Deploy to staging
PULUMI_STACK=staging ./scripts/pulumi-deploy.sh

# Deploy to production
PULUMI_STACK=production ./scripts/pulumi-deploy.sh
```

## Project Structure

```
pulumi/
├── __main__.py              # Main infrastructure code
├── requirements.txt         # Python dependencies
├── Pulumi.yaml             # Project configuration
├── Pulumi.production.yaml  # Production stack config
└── Pulumi.staging.yaml     # Staging stack config
```

## Key Pulumi Commands

```bash
# Preview changes
pulumi preview

# Deploy infrastructure
pulumi up

# Show current stack outputs
pulumi stack output

# List all stacks
pulumi stack ls

# Destroy infrastructure
pulumi destroy

# Show stack history
pulumi history
```

## Customizing Infrastructure

Edit `pulumi/__main__.py` to modify infrastructure:

```python
# Example: Change container resources
container_cpu = config.get_int("container_cpu") or 512  # Increase CPU
container_memory = config.get_int("container_memory") or 1024  # Increase memory

# Example: Add environment variables
container_definitions = [{
    "environment": [
        {"name": "ENVIRONMENT", "value": environment},
        {"name": "API_KEY", "value": config.get_secret("api_key")}  # Secret value
    ]
}]

# Example: Add custom domain
if config.get("enable_cdn"):
    cdn = aws.cloudfront.Distribution("cdn", ...)
```

## CI/CD with GitHub Actions

The repository includes `.github/workflows/pulumi-deploy.yml` for automated deployments:

1. **Add GitHub Secrets**:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `PULUMI_ACCESS_TOKEN` (from pulumi.com)

2. **Deploy on Push**:
   - Commits to `main` deploy to production
   - Manual workflow dispatch for other stacks

## Managing Secrets

Pulumi encrypts secrets automatically:

```bash
# Set a secret
pulumi config set --secret database_password mySecretPass123

# Use in code
password = config.get_secret("database_password")
```

## Monitoring and Troubleshooting

### View Application Logs

```bash
# Get log group name
cd pulumi
LOG_GROUP=$(pulumi stack output log_group_name)

# View logs
aws logs tail $LOG_GROUP --follow
```

### Check Service Status

```bash
cd pulumi
CLUSTER=$(pulumi stack output ecs_cluster_name)
SERVICE=$(pulumi stack output ecs_service_name)

aws ecs describe-services --cluster $CLUSTER --services $SERVICE
```

### Common Issues

1. **Pulumi up fails**
   - Check AWS credentials: `aws sts get-caller-identity`
   - Verify Pulumi login: `pulumi whoami`
   - Review preview: `pulumi preview --diff`

2. **Container fails to start**
   - Check ECR image: `pulumi stack output ecr_repository_url`
   - Review task logs in CloudWatch
   - Verify health check endpoint

3. **Domain not working**
   - Ensure Route53 hosted zone exists
   - Check certificate validation in ACM
   - Verify DNS propagation

## Cost Optimization

```python
# Use Fargate Spot for non-production
if environment != "production":
    capacity_providers = ["FARGATE_SPOT"]
    
# Configure auto-scaling
scaling_policy = {
    "target_value": 50.0,  # Lower threshold for aggressive scaling
    "scale_in_cooldown": 600,  # Longer cooldown to prevent flapping
}
```

## Advanced Features

### 1. Blue-Green Deployments

```python
deployment_configuration = {
    "deployment_circuit_breaker": {
        "enable": True,
        "rollback": True
    },
    "maximum_percent": 200,
    "minimum_healthy_percent": 100
}
```

### 2. Custom Metrics

```python
custom_metric = aws.cloudwatch.MetricAlarm(
    "response-time-alarm",
    comparison_operator="GreaterThanThreshold",
    evaluation_periods=2,
    metric_name="TargetResponseTime",
    namespace="AWS/ApplicationELB",
    period=300,
    statistic="Average",
    threshold=1.0,
    alarm_actions=[sns_topic.arn]
)
```

### 3. Multi-Region Deployment

```python
# Create providers for multiple regions
us_east_1 = aws.Provider("us-east-1", region="us-east-1")
eu_west_1 = aws.Provider("eu-west-1", region="eu-west-1")

# Deploy resources to specific regions
us_alb = aws.lb.LoadBalancer("us-alb", opts=pulumi.ResourceOptions(provider=us_east_1))
eu_alb = aws.lb.LoadBalancer("eu-alb", opts=pulumi.ResourceOptions(provider=eu_west_1))
```

## Importing Existing AWS Resources

If you have existing AWS resources to import:

```bash
# Import an existing ECS cluster
pulumi import aws:ecs/cluster:Cluster main <cluster-arn>

# Import an existing load balancer
pulumi import aws:lb/loadBalancer:LoadBalancer alb <load-balancer-arn>
```

## Cleanup

To remove all resources:

```bash
# Destroy infrastructure
./scripts/pulumi-destroy.sh

# Or manually
cd pulumi
pulumi destroy
pulumi stack rm <stack-name>
```

## Why Choose Pulumi?

| Feature | Benefit |
|---------|---------|
| **Native Python** | Use familiar language constructs, libraries, and tools |
| **Full IDE Support** | IntelliSense, refactoring, and debugging |
| **Real Testing** | Write unit tests for your infrastructure |
| **Type Safety** | Catch errors at compile time, not runtime |
| **Built-in Secrets** | Automatic encryption of sensitive values |
| **State Management** | Automatic state locking and encryption |
| **Policy as Code** | Enforce compliance and best practices |

## Support

- [Pulumi Documentation](https://www.pulumi.com/docs/)
- [Pulumi AWS Provider](https://www.pulumi.com/registry/packages/aws/)
- [Pulumi Examples](https://github.com/pulumi/examples)
- Check `pulumi about` for version info
- Use `pulumi refresh` to sync state