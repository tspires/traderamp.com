# GoDaddy Domain Setup Guide for TradeRamp.com

## Overview
Since AWS ALB doesn't support static IPs and GoDaddy doesn't allow CNAME records on root domains, we'll use:
1. Domain forwarding for the root domain (traderamp.com → www.traderamp.com)
2. CNAME record for www subdomain pointing to the ALB

## Step 1: Set Up Domain Forwarding (Root Domain)

### In GoDaddy:
1. **Log in** to your GoDaddy account
2. Go to **"My Products"** → **"Domains"**
3. Find **traderamp.com** and click **"Manage"**
4. Scroll down to **"Forwarding"** section (or click "Forwarding" in the menu)
5. Click **"Add"** or **"Manage"** next to Domain forwarding
6. Configure forwarding:
   - **Forward to**: `https://www.traderamp.com`
   - **Forward Type**: Select **"Permanent (301)"**
   - **Forward Settings**: Check **"Forward with masking"** OFF (unchecked)
   - Click **"Save"**

## Step 2: Add CNAME Record for WWW Subdomain

### In GoDaddy DNS:
1. In the same domain management page, click **"DNS"** or **"Manage DNS"**
2. In the DNS Records section, click **"Add"**
3. Create new record:
   - **Type**: `CNAME`
   - **Name**: `www`
   - **Value**: `traderamp-dev-alb-95b0200-1783108054.us-east-1.elb.amazonaws.com`
   - **TTL**: `600` (or lowest available)
   - Click **"Save"**

## Step 3: Add DNS Validation for SSL Certificate

While you're in DNS settings, add the certificate validation record:
1. Click **"Add"** in DNS Records
2. Create validation record:
   - **Type**: `CNAME`
   - **Name**: `_11f5533cca910c74f775ca17071297c1`
   - **Value**: `_cd03a8aa6dae8863f7fab4b8a8ecd6ff.xlfgrmvvlj.acm-validations.aws.`
   - **TTL**: `600`
   - Click **"Save"**

## Step 4: Remove Conflicting A Records

**Important**: Remove any A records for @ or www that might conflict:
1. Look for any records with:
   - Type: `A` and Name: `@`
   - Type: `A` and Name: `www`
2. Delete these records (they would override the forwarding/CNAME)

## Expected DNS Configuration

After setup, you should have:
- **Domain Forwarding**: traderamp.com → https://www.traderamp.com
- **CNAME Record**: www → traderamp-dev-alb-95b0200-1783108054.us-east-1.elb.amazonaws.com
- **CNAME Record**: _11f5533cca910c74f775ca17071297c1 → [ACM validation value]

## Timeline
- Domain forwarding: Takes effect in 5-30 minutes
- DNS changes: Can take up to 48 hours to propagate globally (usually 1-4 hours)
- SSL certificate: Will validate within 30 minutes after DNS propagates

## Testing

### 1. Test DNS propagation:
```bash
# Check www CNAME
nslookup www.traderamp.com

# Should eventually show:
# www.traderamp.com    canonical name = traderamp-dev-alb-95b0200-1783108054.us-east-1.elb.amazonaws.com
```

### 2. Test forwarding:
```bash
# Test root domain redirect
curl -I http://traderamp.com

# Should show:
# HTTP/1.1 301 Moved Permanently
# Location: https://www.traderamp.com
```

### 3. Test certificate status:
```bash
cd /path/to/project
./scripts/check-certificate-status.sh
```

## Alternative: Using GoDaddy's Website Builder Redirect

If domain forwarding isn't available in your plan:
1. Use GoDaddy's free website builder
2. Create a simple page that redirects to www
3. Or upgrade to a plan that includes domain forwarding

## Notes
- The 301 redirect is SEO-friendly and tells search engines the move is permanent
- Don't use "masking" as it uses frames and can cause issues
- Once SSL is validated, both http:// and https:// will work
- The ALB will handle HTTP → HTTPS redirect

## Troubleshooting

**Forwarding not working?**
- Check if you have any A records that need to be removed
- Ensure forwarding is set to 301 permanent
- Wait for DNS propagation (up to 48 hours)

**Certificate not validating?**
- Ensure the CNAME record name doesn't include ".traderamp.com" (GoDaddy adds it automatically)
- Check record with: `nslookup _11f5533cca910c74f775ca17071297c1.traderamp.com`

**Still having issues?**
- Clear browser cache and try incognito/private mode
- Try from different network/device
- Check DNS propagation at: https://dnschecker.org/