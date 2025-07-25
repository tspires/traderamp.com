# TradeRamp Production Deployment Guide

This guide provides step-by-step instructions for deploying TradeRamp to production.

## 📋 Pre-Deployment Checklist

Before deploying, ensure you have:

- [ ] AWS Account with appropriate permissions
- [ ] Domain name registered (optional)
- [ ] SSL certificate in AWS Certificate Manager (if using custom domain)
- [ ] Node.js 14+ and npm installed
- [ ] Python 3.8+ installed
- [ ] Docker installed
- [ ] AWS CLI configured
- [ ] Pulumi CLI installed

## 🚀 Quick Start

For experienced developers, use these quick commands:

```bash
# Install dependencies and build
make install
make build

# Deploy to AWS
make deploy
```

## 📦 Detailed Deployment Steps

### 1. Environment Setup

```bash
# Clone the repository
git clone https://github.com/your-repo/traderamp.com.git
cd traderamp.com

# Create environment file from template
make env-template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 2. Install Dependencies

```bash
# Install all project dependencies
make install

# Or manually:
npm install
pip3 install -r requirements.txt
pip3 install -r pulumi/requirements.txt
```

### 3. Build for Production

```bash
# Run the production build
make build

# This will:
# - Minify and concatenate CSS
# - Minify and concatenate JavaScript
# - Optimize images
# - Generate production HTML
# - Create dist/ directory with all assets
```

### 4. Test Locally

```bash
# Start local server to test the build
make serve

# Visit http://localhost:8000 to verify everything works
```

### 5. Infrastructure Setup with Pulumi

```bash
# Navigate to Pulumi directory
cd pulumi

# Initialize Pulumi stack (first time only)
pulumi stack init production

# Configure AWS region
pulumi config set aws:region us-east-1

# Configure project settings
pulumi config set traderamp:projectName traderamp
pulumi config set traderamp:environment production

# If using custom domain
pulumi config set traderamp:domainName traderamp.com

# Preview infrastructure changes
pulumi preview

# Deploy infrastructure
pulumi up --yes

# Note the outputs (ALB URL, CloudFront distribution, etc.)
```

### 6. Build and Push Docker Image

```bash
# Build Docker image
make docker-build

# Test locally
make docker-run
# Visit http://localhost:8080

# Push to ECR
make ecr-push
```

### 7. Deploy Application

The application will be automatically deployed by ECS after pushing to ECR.

To manually trigger a deployment:

```bash
# Force new deployment
aws ecs update-service \
  --cluster traderamp-production \
  --service traderamp-app \
  --force-new-deployment \
  --region us-east-1
```

## 🔧 Configuration

### Environment Variables

Key environment variables to configure:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_PROFILE=default

# Domain Configuration
DOMAIN_NAME=traderamp.com
CERTIFICATE_ARN=arn:aws:acm:us-east-1:...

# Application
ENVIRONMENT=production
PROJECT_NAME=traderamp

# Analytics (optional)
GOOGLE_ANALYTICS_ID=UA-XXXXXXXXX-X
FACEBOOK_PIXEL_ID=XXXXXXXXXXXXXXX
```

### DNS Configuration

If using a custom domain:

1. Get the ALB or CloudFront URL from Pulumi outputs
2. Create CNAME record pointing to the URL
3. Wait for DNS propagation (5-30 minutes)

### SSL Certificate

For HTTPS with custom domain:

1. Request certificate in AWS Certificate Manager
2. Validate domain ownership
3. Note the certificate ARN
4. Add to Pulumi configuration

## 📊 Monitoring

### CloudWatch Dashboards

Access dashboards at:
https://console.aws.amazon.com/cloudwatch/

Key metrics to monitor:
- ECS Service CPU/Memory utilization
- ALB request count and latency
- Error rates (4xx, 5xx)
- Container health checks

### Logs

View application logs:

```bash
# View recent logs
aws logs tail /ecs/traderamp-production --follow

# Search logs
aws logs filter-log-events \
  --log-group-name /ecs/traderamp-production \
  --filter-pattern "ERROR"
```

## 🔄 Updates and Rollbacks

### Updating the Application

```bash
# Make changes to code
# ...

# Build and test
make build
make test

# Deploy update
make deploy
```

### Rolling Back

```bash
# Via Pulumi (infrastructure)
cd pulumi
pulumi stack history
pulumi stack export > backup.json
pulumi up --target-dependents --target urn:pulumi:...

# Via ECS (application)
aws ecs update-service \
  --cluster traderamp-production \
  --service traderamp-app \
  --task-definition traderamp-app:PREVIOUS_REVISION
```

## 🚨 Troubleshooting

### Common Issues

1. **Build Fails**
   ```bash
   # Clean and rebuild
   make clean
   make install
   make build
   ```

2. **Docker Issues**
   ```bash
   # Reset Docker
   docker system prune -a
   make docker-build
   ```

3. **Deployment Fails**
   ```bash
   # Check Pulumi state
   pulumi stack
   pulumi refresh
   
   # Check AWS resources
   aws ecs describe-services --cluster traderamp-production
   ```

4. **Application Not Accessible**
   - Check security groups
   - Verify target group health
   - Check ECS task logs
   - Verify DNS configuration

### Debug Commands

```bash
# Check ECS service status
aws ecs describe-services \
  --cluster traderamp-production \
  --services traderamp-app

# Check running tasks
aws ecs list-tasks \
  --cluster traderamp-production \
  --service-name traderamp-app

# Check ALB target health
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:...
```

## 📈 Performance Optimization

### CDN Configuration

CloudFront is automatically configured with:
- Cache static assets (images, CSS, JS)
- Compress text files
- HTTP/2 support
- Edge locations worldwide

### Auto-Scaling

ECS Service auto-scales based on:
- CPU utilization (target: 70%)
- Memory utilization (target: 70%)
- Min instances: 1
- Max instances: 4

## 🔐 Security

### Security Checklist

- [ ] Remove all console.log statements
- [ ] Update all dependencies
- [ ] Run security scan: `make security-scan`
- [ ] Enable WAF rules in production
- [ ] Review security group rules
- [ ] Enable CloudTrail logging
- [ ] Set up alerts for suspicious activity

### SSL/TLS

- TLS 1.2+ enforced
- Strong cipher suites only
- HSTS headers enabled
- Regular certificate rotation

## 📞 Support

For issues or questions:

1. Check CloudWatch logs
2. Review this guide
3. Check AWS service health
4. Contact your DevOps team

## 🎯 Next Steps

After successful deployment:

1. Set up monitoring alerts
2. Configure backups
3. Document any custom configurations
4. Schedule regular security reviews
5. Plan for disaster recovery

---

**Remember**: Always test in staging before deploying to production!