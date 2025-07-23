#!/bin/bash
set -e

# Production cleanup script for TradeRamp
# This script fixes critical issues before deployment

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Backup function
backup_file() {
    if [ -f "$1" ]; then
        cp "$1" "$1.backup-$(date +%Y%m%d-%H%M%S)"
        print_status "Backed up $1"
    fi
}

print_warning "Starting production cleanup..."
echo ""

# 1. Fix broken logo link
print_status "Fixing logo link..."
backup_file "index.html"
sed -i.tmp 's|href="index-2.html"|href="/"|g' index.html && rm index.html.tmp

# 2. Update meta author
print_status "Updating meta author..."
sed -i.tmp 's|content="zytheme"|content="TradeRamp"|g' index.html && rm index.html.tmp

# 3. Remove console.error from schedule-form.js
if [ -f "assets/js/schedule-form.js" ]; then
    print_status "Removing console.error from schedule-form.js..."
    backup_file "assets/js/schedule-form.js"
    sed -i.tmp 's|console\.error|// console.error|g' assets/js/schedule-form.js && rm assets/js/schedule-form.js.tmp
fi

# 4. Remove console.log from app.js
if [ -f "assets/js/app.js" ]; then
    print_status "Cleaning console logs from app.js..."
    backup_file "assets/js/app.js"
    sed -i.tmp 's|console\.log|// console.log|g' assets/js/app.js && rm assets/js/app.js.tmp
fi

# 5. Update copyright year to current year
CURRENT_YEAR=$(date +%Y)
print_status "Updating copyright year to $CURRENT_YEAR..."
sed -i.tmp "s|© TradeRamp 2024|© TradeRamp $CURRENT_YEAR|g" index.html && rm index.html.tmp

# 6. Create a basic 404 page if it doesn't exist
if [ ! -f "404.html" ]; then
    print_status "Creating 404 error page..."
    cat > 404.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Page Not Found - TradeRamp</title>
    <link href="assets/css/bootstrap.min.css" rel="stylesheet">
    <link href="assets/css/style.css" rel="stylesheet">
</head>
<body>
    <div class="container text-center" style="padding: 100px 0;">
        <h1>404 - Page Not Found</h1>
        <p>Sorry, the page you're looking for doesn't exist.</p>
        <a href="/" class="btn btn--primary btn--rounded">Go to Homepage</a>
    </div>
</body>
</html>
EOF
fi

# 7. Create robots.txt if it doesn't exist
if [ ! -f "robots.txt" ]; then
    print_status "Creating robots.txt..."
    cat > robots.txt << 'EOF'
User-agent: *
Allow: /
Disallow: /assets/js/
Disallow: /assets/css/
Sitemap: https://traderamp.com/sitemap.xml
EOF
fi

# 8. Create a basic sitemap.xml
if [ ! -f "sitemap.xml" ]; then
    print_status "Creating sitemap.xml..."
    cat > sitemap.xml << EOF
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://traderamp.com/</loc>
        <lastmod>$(date +%Y-%m-%d)</lastmod>
        <changefreq>weekly</changefreq>
        <priority>1.0</priority>
    </url>
</urlset>
EOF
fi

# 9. Update nginx.conf for better security
if [ -f "nginx.conf" ]; then
    print_status "Updating nginx security headers..."
    backup_file "nginx.conf"
    # Remove unsafe-inline and unsafe-eval from CSP
    sed -i.tmp "s|'unsafe-inline' 'unsafe-eval'||g" nginx.conf && rm nginx.conf.tmp
fi

# 10. Check for exposed sensitive data
print_status "Checking for exposed sensitive data..."
SENSITIVE_PATTERNS="password|secret|api[_-]key|private[_-]key|access[_-]token"
if grep -r -i -E "$SENSITIVE_PATTERNS" --include="*.js" --include="*.html" --include="*.css" . 2>/dev/null | grep -v "node_modules" | grep -v ".git"; then
    print_error "Found potential sensitive data in files above. Please review!"
else
    print_status "No obvious sensitive data found"
fi

# 11. Create .env.example if it doesn't exist
if [ ! -f ".env.example" ]; then
    print_status "Creating .env.example..."
    cat > .env.example << 'EOF'
# API Configuration
API_ENDPOINT=https://api.traderamp.com
FORM_ENDPOINT=/api/schedule-call

# Email Service
EMAIL_SERVICE_API_KEY=your-api-key-here
NOTIFICATION_EMAIL=leads@traderamp.com

# Analytics (optional)
GA_TRACKING_ID=G-XXXXXXXXXX
FB_PIXEL_ID=XXXXXXXXXXXXXXXX

# Environment
NODE_ENV=production
EOF
fi

# Summary
echo ""
print_status "Production cleanup completed!"
echo ""
print_warning "Manual tasks still required:"
echo "  - Implement form backend (see PRODUCTION-CLEANUP.md)"
echo "  - Add Privacy Policy and Terms of Service pages"
echo "  - Replace stock images with real photos"
echo "  - Configure analytics tracking codes"
echo "  - Set up email service integration"
echo "  - Test all functionality thoroughly"
echo ""
print_warning "Backup files created with .backup-* extension"
echo ""

# Optional: Run a simple HTTP server to test locally
read -p "Would you like to test the site locally? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Starting local server on http://localhost:8080"
    print_warning "Press Ctrl+C to stop"
    python3 -m http.server 8080
fi