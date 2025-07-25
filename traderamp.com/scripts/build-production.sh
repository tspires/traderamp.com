#!/bin/bash

# Production Build Script for TradeRamp
# This script prepares the site for production deployment

set -e

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Check for command line arguments
BUILD_MODE="${1:-all}"

# Create dist directory if it doesn't exist
mkdir -p dist/assets/css dist/assets/js dist/assets/images dist/assets/fonts

# Function to build CSS only
build_css() {
    echo "📦 Building CSS..."

# Define CSS files in loading order
CSS_FILES=(
    "assets/css/library/bootstrap.min.css"
    "assets/css/library/font-awesome.min.css"
    "assets/css/library/animate.min.css"
    "assets/css/library/stroke-gap-icons.css"
    "assets/css/cons.css"
    "assets/css/external.css"
    "assets/css/base.css"
    "assets/css/layout.css"
    "assets/css/components.css"
    "assets/css/modules/buttons.css"
    "assets/css/modules/forms.css"
    "assets/css/modules/header.css"
    "assets/css/style.css"
    "assets/css/main.css"
)

# Concatenate CSS files
echo "Concatenating CSS files..."
> dist/assets/css/app.css
for css_file in "${CSS_FILES[@]}"; do
    if [ -f "$css_file" ]; then
        echo "/* Source: $css_file */" >> dist/assets/css/app.css
        cat "$css_file" >> dist/assets/css/app.css
        echo "" >> dist/assets/css/app.css
    else
        echo "Warning: CSS file not found: $css_file"
    fi
done

# Check if cssmin is available, if not provide instructions
if ! command -v cssmin &> /dev/null; then
    echo "ℹ️  cssmin not found. To install: pip install cssmin"
    echo "   For now, copying concatenated CSS as-is..."
    cp dist/assets/css/app.css dist/assets/css/app.min.css
else
    echo "Minifying CSS..."
    cssmin < dist/assets/css/app.css > dist/assets/css/app.min.css
fi

echo "📦 Building JavaScript..."

# Define JS files in loading order
JS_FILES=(
    "assets/js/jquery-2.2.4.min.js"
    "assets/js/plugins/bootstrap.js"
    "assets/js/plugins/owl.carousel.js"
    "assets/js/plugins/jquery.mb.YTPlayer.min.js"
    "assets/js/plugins.js"
    "assets/js/utils/error-handler.js"
    "assets/js/utils/form-validator.js"
    "assets/js/functions.js"
    "assets/js/schedule-form.js"
    "assets/js/app.js"
)

# Concatenate JS files
echo "Concatenating JavaScript files..."
> dist/assets/js/app.js
for js_file in "${JS_FILES[@]}"; do
    if [ -f "$js_file" ]; then
        echo "/* Source: $js_file */" >> dist/assets/js/app.js
        cat "$js_file" >> dist/assets/js/app.js
        echo "" >> dist/assets/js/app.js
    else
        echo "Warning: JS file not found: $js_file"
    fi
done

# Check if terser is available
if ! command -v terser &> /dev/null; then
    echo "ℹ️  terser not found. To install: npm install -g terser"
    echo "   For now, copying concatenated JS as-is..."
    cp dist/assets/js/app.js dist/assets/js/app.min.js
else
    echo "Minifying JavaScript..."
    terser dist/assets/js/app.js -o dist/assets/js/app.min.js --compress --mangle
fi

echo "🖼️  Copying images and fonts..."
cp -r assets/images/* dist/assets/images/
cp -r assets/fonts/* dist/assets/fonts/

echo "📄 Processing HTML..."
# Copy HTML files to dist
cp index.html dist/index.html
cp 404.html dist/404.html
cp robots.txt dist/robots.txt
cp sitemap.xml dist/sitemap.xml

# Update HTML to use minified assets
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' 's|<!-- CSS Files -->.*<!-- /CSS Files -->|<link href="assets/css/app.min.css" rel="stylesheet">|' dist/index.html
    sed -i '' 's|<!-- JS Files -->.*<!-- /JS Files -->|<script src="assets/js/app.min.js"></script>|' dist/index.html
    
    # Remove individual CSS links
    sed -i '' '/<link href="assets\/css\/library\/bootstrap.min.css"/d' dist/index.html
    sed -i '' '/<link href="assets\/css\/cons.css"/d' dist/index.html
    sed -i '' '/<link href="assets\/css\/external.css"/d' dist/index.html
    sed -i '' '/<link href="assets\/css\/style.css"/d' dist/index.html
    sed -i '' '/<link href="assets\/css\/main.css"/d' dist/index.html
    
    # Update to use single minified CSS
    sed -i '' 's|</title>|</title>\
    <link href="assets/css/app.min.css" rel="stylesheet">|' dist/index.html
else
    # Linux
    sed -i 's|<!-- CSS Files -->.*<!-- /CSS Files -->|<link href="assets/css/app.min.css" rel="stylesheet">|' dist/index.html
    sed -i 's|<!-- JS Files -->.*<!-- /JS Files -->|<script src="assets/js/app.min.js"></script>|' dist/index.html
fi

echo "🧹 Cleaning up..."
# Remove console.log and console.error statements from production JS
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' 's/console\.log[^;]*;//g' dist/assets/js/app.min.js
    sed -i '' 's/console\.error[^;]*;//g' dist/assets/js/app.min.js
else
    sed -i 's/console\.log[^;]*;//g' dist/assets/js/app.min.js
    sed -i 's/console\.error[^;]*;//g' dist/assets/js/app.min.js
fi

echo "📊 Build Summary:"
echo "==================="
if [ -f dist/assets/css/app.min.css ]; then
    css_size=$(du -h dist/assets/css/app.min.css | cut -f1)
    echo "CSS Bundle: $css_size"
fi
if [ -f dist/assets/js/app.min.js ]; then
    js_size=$(du -h dist/assets/js/app.min.js | cut -f1)
    echo "JS Bundle: $js_size"
fi

echo ""
echo "✅ Production build complete!"
echo "   Output directory: $PROJECT_ROOT/dist/"
echo ""
echo "Next steps:"
echo "1. Test the production build locally: cd dist && python -m http.server 8000"
echo "2. Deploy the 'dist' directory to your production server"
echo ""

# Create deployment instructions
cat > dist/DEPLOYMENT.md << EOF
# Deployment Instructions

This directory contains the production-ready build of TradeRamp.

## Files to Deploy
- index.html
- 404.html
- robots.txt
- sitemap.xml
- assets/
  - css/app.min.css
  - js/app.min.js
  - images/
  - fonts/

## Deployment Steps
1. Upload all files to your web server or S3 bucket
2. Ensure proper MIME types are set for all file extensions
3. Configure your web server (nginx/Apache) or CDN
4. Set up SSL certificate
5. Test the deployment

## Post-Deployment Checklist
- [ ] Verify all pages load correctly
- [ ] Test form submission
- [ ] Check that all images load
- [ ] Verify CSS and JS are loading
- [ ] Test on mobile devices
- [ ] Check browser console for errors
EOF

echo "📝 Deployment instructions created in dist/DEPLOYMENT.md"