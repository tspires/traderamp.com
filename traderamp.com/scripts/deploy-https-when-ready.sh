#\!/bin/bash
CERT_ARN="arn:aws:acm:us-east-1:211125719399:certificate/f6854ceb-27e0-4f72-bfe7-8a0e74699a82"
REGION="us-east-1"

echo "Checking certificate status..."
STATUS=$(aws acm describe-certificate --certificate-arn "$CERT_ARN" --region "$REGION" --query 'Certificate.Status' --output text)

if [ "$STATUS" == "ISSUED" ]; then
    echo "Certificate is validated\!"
    echo ""
    echo "Deploying HTTPS listener..."
    
    cd "$(dirname "$0")/../pulumi" || exit 1
    
    pulumi config set certificate_arn "$CERT_ARN"
    pulumi up --yes --skip-preview
    
    echo ""
    echo "HTTPS setup complete\! Your site is now available at:"
    echo "  - https://www.traderamp.com"
    echo "  - https://traderamp.com (after domain forwarding is configured)"
    
elif [ "$STATUS" == "PENDING_VALIDATION" ]; then
    echo "Certificate is still pending validation"
    echo ""
    echo "To complete SSL setup, add this CNAME record in GoDaddy DNS:"
    echo ""
    echo "Type: CNAME"
    echo "Name: _11f5533cca910c74f775ca17071297c1"
    echo "Value: _cd03a8aa6dae8863f7fab4b8a8ecd6ff.xlfgrmvvlj.acm-validations.aws."
    echo "TTL: 600"
    echo ""
    echo "Once added, the certificate will validate within 30 minutes."
    echo "Then run this script again or use: ./wait-and-deploy-https.sh"
else
    echo "Unexpected certificate status: $STATUS"
    exit 1
fi
EOF < /dev/null