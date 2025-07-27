#!/bin/bash
# Check ACM certificate validation status

CERT_ARN="arn:aws:acm:us-east-1:211125719399:certificate/f6854ceb-27e0-4f72-bfe7-8a0e74699a82"
REGION="us-east-1"

echo "Checking certificate status for traderamp.com..."
echo "Certificate ARN: $CERT_ARN"
echo ""

# Get certificate details
STATUS=$(aws acm describe-certificate \
  --certificate-arn "$CERT_ARN" \
  --region "$REGION" \
  --query 'Certificate.Status' \
  --output text)

echo "Current Status: $STATUS"

if [ "$STATUS" == "PENDING_VALIDATION" ]; then
    echo ""
    echo "Certificate is pending validation. Please add these DNS records to GoDaddy:"
    echo ""
    aws acm describe-certificate \
      --certificate-arn "$CERT_ARN" \
      --region "$REGION" \
      --query 'Certificate.DomainValidationOptions[0].ResourceRecord' \
      --output table
elif [ "$STATUS" == "ISSUED" ]; then
    echo ""
    echo "✅ Certificate is validated and ready to use!"
    echo "You can now run: pulumi config set domain_name traderamp.com && pulumi up"
else
    echo ""
    echo "Certificate status: $STATUS"
fi