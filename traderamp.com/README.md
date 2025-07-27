# TradeRamp - IT Solutions for Trade Companies

TradeRamp provides specialized IT solutions and digital marketing services for trade companies including plumbers, electricians, HVAC contractors, and more.

## 🚀 Features

- Responsive design optimized for all devices
- HubSpot form integration for lead capture
- AWS-hosted infrastructure with auto-scaling
- SEO-optimized content
- Performance-optimized assets

## 📋 Quick Start

### Development

```bash
# Install dependencies
make install

# Start local development server
make serve

# Access at http://localhost:8000
```

### Production Build

```bash
# Create production build
make build

# Deploy to AWS
make deploy
```

## 🔧 Configuration

### HubSpot Form Setup

The contact form uses HubSpot for lead management. To configure:

1. Get your HubSpot Portal ID and Form ID
2. Update the values in `index.html`:
   ```html
   <div class="hs-form-frame" 
        data-form-id="YOUR-FORM-ID" 
        data-portal-id="YOUR-PORTAL-ID">
   ```
3. See `HUBSPOT-SETUP.md` for detailed instructions

### Environment Variables

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Required variables:
- `AWS_REGION` - AWS region for deployment
- `DOMAIN_NAME` - Your domain (optional)
- `CERTIFICATE_ARN` - SSL certificate ARN (if using custom domain)

## 📁 Project Structure

```
traderamp.com/
├── assets/          # Static assets (CSS, JS, images)
├── dist/            # Production build output
├── pulumi/          # Infrastructure as code
├── scripts/         # Build and deployment scripts
├── index.html       # Main landing page
├── Makefile         # Build automation
└── package.json     # Node dependencies
```

## 🛠️ Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript (jQuery)
- **Forms**: HubSpot Forms API
- **Infrastructure**: AWS (ECS, ALB, CloudFront)
- **IaC**: Pulumi
- **Build**: Make, Node.js
- **Container**: Docker

## 📚 Documentation

- [Deployment Guide](DEPLOYMENT-GUIDE.md) - Complete deployment instructions
- [HubSpot Setup](HUBSPOT-SETUP.md) - Form configuration guide
- [Cleanup Summary](CLEANUP-SUMMARY.md) - Recent improvements
- [Production Cleanup](PRODUCTION-CLEANUP.md) - Production checklist

## 🔒 Security

- HTTPS enforced via CloudFront
- Content Security Policy headers
- Input validation on all forms
- Regular dependency updates

## 🚨 Important Notes

1. **HubSpot Configuration**: You must configure your HubSpot IDs before the form will work
2. **API Endpoints**: The `/api/schedule-call` endpoint is no longer used (replaced by HubSpot)
3. **Analytics**: Add your Google Analytics and Facebook Pixel IDs to track conversions

## 📈 Performance

- CSS and JS are minified and concatenated
- Images are optimized
- CDN distribution via CloudFront
- Lazy loading for images
- Gzip compression enabled

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Run tests: `make test`
4. Submit a pull request

## 📞 Support

For technical issues, check:
1. Browser console for JavaScript errors
2. CloudWatch logs for server errors
3. HubSpot dashboard for form submissions

## 📄 License

Copyright © 2024 TradeRamp. All rights reserved.