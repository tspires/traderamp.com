# SSL/HTTPS Setup Guide for TradeRamp.com

## Current Status
- Domain: traderamp.com (hosted on GoDaddy)
- ACM Certificate ARN: `arn:aws:acm:us-east-1:211125719399:certificate/f6854ceb-27e0-4f72-bfe7-8a0e74699a82`
- Certificate Status: Pending Validation

## Step 1: Add DNS Validation Records to GoDaddy

You need to add the following CNAME record to your GoDaddy DNS settings:

### DNS Validation Record:
- **Type**: CNAME
- **Name**: `_11f5533cca910c74f775ca17071297c1`
- **Value**: `_cd03a8aa6dae8863f7fab4b8a8ecd6ff.xlfgrmvvlj.acm-validations.aws.`
- **TTL**: 600 (or lowest available)

### How to Add in GoDaddy:
1. Log in to your GoDaddy account
2. Go to "My Products" → "Domains"
3. Find traderamp.com and click "DNS"
4. Click "Add" in the DNS Records section
5. Select Type: CNAME
6. Enter the Name and Value from above (GoDaddy will automatically append .traderamp.com)
7. Save the record

## Step 2: Wait for Certificate Validation
After adding the DNS record, AWS will validate the certificate. This usually takes 5-30 minutes.

Check certificate status:
```bash
aws acm describe-certificate \
  --certificate-arn arn:aws:acm:us-east-1:211125719399:certificate/f6854ceb-27e0-4f72-bfe7-8a0e74699a82 \
  --region us-east-1 \
  --query 'Certificate.Status'
```

## Step 3: Update Pulumi Configuration
Once the certificate is validated (status: ISSUED), run:
```bash
cd pulumi
pulumi config set domain_name traderamp.com
pulumi config set create_dns_records false  # Since we're using GoDaddy
pulumi up --yes
```

## Step 4: Add A Record for Domain
After Pulumi completes, add an A record in GoDaddy pointing to the ALB:

1. In GoDaddy DNS settings, add:
   - **Type**: A
   - **Name**: @ (for root domain)
   - **Value**: [ALB IP address - see note below]
   - **TTL**: 600

Note: Since ALBs use dynamic IPs, it's better to use a CNAME, but GoDaddy doesn't allow CNAME on root domain. 
Options:
- Use www.traderamp.com with CNAME pointing to ALB DNS name
- Use a service like Route53 for DNS management
- Use GoDaddy's forwarding feature

## Alternative: Migrate to Route53 (Recommended)
For better integration with AWS services:
1. Create Route53 hosted zone
2. Update nameservers in GoDaddy to point to Route53
3. Manage all DNS records in Route53
4. Use alias records for ALB (no static IP needed)

## Current Infrastructure
- ALB URL: http://traderamp-dev-alb-95b0200-1783108054.us-east-1.elb.amazonaws.com
- The website is currently accessible via HTTP on this URL