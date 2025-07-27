#!/bin/bash
# Wait for certificate validation and deploy HTTPS

CERT_ARN="arn:aws:acm:us-east-1:211125719399:certificate/f6854ceb-27e0-4f72-bfe7-8a0e74699a82"
REGION="us-east-1"
CHECK_INTERVAL=30  # Check every 30 seconds

echo "Monitoring certificate validation status..."
echo "Certificate ARN: $CERT_ARN"
echo ""

while true; do
    STATUS=$(aws acm describe-certificate \
        --certificate-arn "$CERT_ARN" \
        --region "$REGION" \
        --query 'Certificate.Status' \
        --output text 2>/dev/null)
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Certificate status: $STATUS"
    
    if [ "$STATUS" == "ISSUED" ]; then
        echo ""
        echo "✅ Certificate is validated!"
        echo "Deploying HTTPS listener with Pulumi..."
        
        cd "$(dirname "$0")/../pulumi" || exit 1
        
        # Run Pulumi to create HTTPS listener
        if pulumi up --yes --skip-preview; then
            echo ""
            echo "✅ HTTPS listener deployed successfully!"
            echo ""
            echo "Your website is now available at:"
            echo "  - HTTP:  http://www.traderamp.com"
            echo "  - HTTPS: https://www.traderamp.com"
            echo ""
            echo "Note: DNS propagation may take additional time."
        else
            echo "❌ Failed to deploy HTTPS listener"
            exit 1
        fi
        
        break
    elif [ "$STATUS" == "PENDING_VALIDATION" ]; then
        echo "Still waiting for DNS validation..."
        echo "Make sure you've added the CNAME record to GoDaddy:"
        echo "  Name: _11f5533cca910c74f775ca17071297c1"
        echo "  Value: _cd03a8aa6dae8863f7fab4b8a8ecd6ff.xlfgrmvvlj.acm-validations.aws."
    else
        echo "Unexpected status: $STATUS"
    fi
    
    echo "Checking again in $CHECK_INTERVAL seconds... (Press Ctrl+C to stop)"
    sleep $CHECK_INTERVAL
done