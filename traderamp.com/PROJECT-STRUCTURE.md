# TradeRamp Project Structure

## Overview
This is the TradeRamp website - a static site deployed on AWS using Docker, ECS Fargate, and CloudFront CDN.

## Directory Structure

```
traderamp.com/
├── README.md                    # Main project documentation
├── index.html                   # Homepage
├── privacy-policy.html          # Privacy policy page
├── 404.html                     # Custom 404 error page
├── robots.txt                   # Search engine directives
├── sitemap.xml                  # XML sitemap for SEO
│
├── assets/                      # Static assets
│   ├── css/                     # Stylesheets
│   │   ├── main.css            # Custom styles
│   │   └── modules/            # Modular CSS components
│   ├── js/                     # JavaScript files
│   │   ├── app.js              # Main application JS
│   │   └── hubspot-form.js     # HubSpot form integration
│   └── images/                 # Images and graphics
│       ├── logo/               # Logo files
│       ├── hero/               # Hero section images
│       └── testimonials/       # Client testimonial images
│
├── build-and-deploy.sh         # Main deployment script
├── Dockerfile                  # Docker container definition
├── nginx.conf                  # Main Nginx configuration
├── nginx-site.conf            # Site-specific Nginx config
├── .dockerignore              # Docker build exclusions
├── .gitignore                 # Git exclusions
│
├── pulumi/                    # Infrastructure as Code
│   ├── __main__.py           # Pulumi entry point
│   ├── Pulumi.yaml           # Pulumi project config
│   ├── core/                 # Core infrastructure components
│   ├── providers/            # Cloud provider implementations
│   │   └── aws/             # AWS-specific components
│   └── stacks/              # Infrastructure stacks
│
├── scripts/                   # Utility scripts
│   ├── check-certificate-status.sh
│   ├── configure-hubspot.sh
│   ├── deploy-https-when-ready.sh
│   ├── local-test.sh
│   └── wait-and-deploy-https.sh
│
├── docs/                      # Documentation
│   ├── deployment/           # Deployment guides
│   ├── setup/               # Setup instructions
│   └── development/         # Development notes
│
└── archived-code/            # Old implementations (git-ignored)

```

## Key Files

### Website Files
- `index.html` - Main website with HubSpot form integration
- `assets/css/main.css` - Custom styles including navbar and logo sizing
- `assets/js/hubspot-form.js` - HubSpot form initialization

### Infrastructure
- `Dockerfile` - Nginx Alpine container with health check
- `build-and-deploy.sh` - Builds Docker image and deploys to ECS
- `pulumi/` - Complete AWS infrastructure (VPC, ECS, ALB, CloudFront)

### Configuration
- `nginx-site.conf` - Nginx server configuration with caching rules
- `.dockerignore` - Excludes unnecessary files from Docker build
- `.gitignore` - Excludes cache files, temp files, and archived code

## Deployment

### Quick Deploy
```bash
./build-and-deploy.sh
```

### Infrastructure Updates
```bash
cd pulumi && pulumi up
```

### Local Testing
```bash
python3 -m http.server 8080
# Visit http://localhost:8080
```

## AWS Resources

- **ECS Fargate**: Running containerized Nginx
- **Application Load Balancer**: Public-facing ALB
- **CloudFront CDN**: Global content delivery
- **ECR**: Docker image repository
- **VPC**: Custom network with public subnets

## Environment

- **AWS Region**: us-east-1
- **Container**: nginx:alpine
- **Resources**: 0.25 vCPU, 0.5 GB RAM
- **Estimated Cost**: ~$40-60/month