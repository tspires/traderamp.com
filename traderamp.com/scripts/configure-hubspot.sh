#!/bin/bash

# HubSpot Configuration Script
# This script helps you configure your HubSpot Portal ID and Form ID

echo "================================================="
echo "HubSpot Form Configuration Script"
echo "================================================="
echo ""

# Function to validate Portal ID (should be numeric)
validate_portal_id() {
    if [[ $1 =~ ^[0-9]+$ ]]; then
        return 0
    else
        return 1
    fi
}

# Function to validate Form ID (UUID format)
validate_form_id() {
    if [[ $1 =~ ^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$ ]]; then
        return 0
    else
        return 1
    fi
}

# Default values from caerusc.com
DEFAULT_PORTAL_ID="242471098"
DEFAULT_FORM_ID="a031a33a-709c-4970-8679-5064e825987d"

# Get Portal ID
echo "Default Portal ID from caerusc.com: $DEFAULT_PORTAL_ID"
read -p "Enter your HubSpot Portal ID (press Enter to use default): " PORTAL_ID
if [[ -z "$PORTAL_ID" ]]; then
    PORTAL_ID="$DEFAULT_PORTAL_ID"
    echo "✓ Using default Portal ID: $PORTAL_ID"
else
    if validate_portal_id "$PORTAL_ID"; then
        echo "✓ Valid Portal ID format"
    else
        echo "✗ Invalid Portal ID. Using default: $DEFAULT_PORTAL_ID"
        PORTAL_ID="$DEFAULT_PORTAL_ID"
    fi
fi

# Get Form ID
echo ""
echo "Default Form ID from caerusc.com: $DEFAULT_FORM_ID"
read -p "Enter your HubSpot Form ID (press Enter to use default): " FORM_ID
if [[ -z "$FORM_ID" ]]; then
    FORM_ID="$DEFAULT_FORM_ID"
    echo "✓ Using default Form ID: $FORM_ID"
else
    if validate_form_id "$FORM_ID"; then
        echo "✓ Valid Form ID format"
    else
        echo "✗ Invalid Form ID. Using default: $DEFAULT_FORM_ID"
        FORM_ID="$DEFAULT_FORM_ID"
    fi
fi

echo ""
echo "Configuring HubSpot with:"
echo "Portal ID: $PORTAL_ID"
echo "Form ID: $FORM_ID"
echo ""

# Get the parent directory path
PARENT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Update index.html
echo "Updating index.html..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/data-form-id=\"YOUR-HUBSPOT-FORM-ID\"/data-form-id=\"$FORM_ID\"/g" "$PARENT_DIR/index.html"
    sed -i '' "s/data-portal-id=\"YOUR-HUBSPOT-PORTAL-ID\"/data-portal-id=\"$PORTAL_ID\"/g" "$PARENT_DIR/index.html"
else
    # Linux
    sed -i "s/data-form-id=\"YOUR-HUBSPOT-FORM-ID\"/data-form-id=\"$FORM_ID\"/g" "$PARENT_DIR/index.html"
    sed -i "s/data-portal-id=\"YOUR-HUBSPOT-PORTAL-ID\"/data-portal-id=\"$PORTAL_ID\"/g" "$PARENT_DIR/index.html"
fi

# Update hubspot-form.js
echo "Updating hubspot-form.js..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/portalId: 'YOUR-HUBSPOT-PORTAL-ID'/portalId: '$PORTAL_ID'/g" "$PARENT_DIR/assets/js/hubspot-form.js"
    sed -i '' "s/formId: 'YOUR-HUBSPOT-FORM-ID'/formId: '$FORM_ID'/g" "$PARENT_DIR/assets/js/hubspot-form.js"
else
    # Linux
    sed -i "s/portalId: 'YOUR-HUBSPOT-PORTAL-ID'/portalId: '$PORTAL_ID'/g" "$PARENT_DIR/assets/js/hubspot-form.js"
    sed -i "s/formId: 'YOUR-HUBSPOT-FORM-ID'/formId: '$FORM_ID'/g" "$PARENT_DIR/assets/js/hubspot-form.js"
fi

echo ""
echo "✓ Configuration complete!"
echo ""
echo "Next steps:"
echo "1. Test the form by opening index.html in a browser"
echo "2. Submit a test entry to verify it appears in HubSpot"
echo "3. Commit the changes: git add -A && git commit -m 'Configure HubSpot form IDs'"
echo ""
echo "If you need to find your IDs again, check HUBSPOT-ID-GUIDE.md"
