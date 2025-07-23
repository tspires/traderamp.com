# Production Deployment Cleanup Checklist

This checklist covers all necessary cleanup tasks before deploying TradeRamp to production.

## 🚨 Critical Issues (Must Fix)

### 1. Form Backend Implementation
- [ ] Implement actual backend API endpoint for `/api/schedule-call`
- [ ] Options:
  - AWS Lambda + API Gateway
  - Formspree or similar service
  - Email service integration (SendGrid, SES)
- [ ] Add server-side validation
- [ ] Implement CSRF protection

### 2. Remove Development Artifacts
- [ ] Remove console.log/console.error statements
  - `schedule-form.js` line 139
  - `app.js` throughout
- [ ] Remove alert() in `app.js` line 332
- [ ] Remove or configure Mailchimp URL placeholder
- [ ] Update meta author from "zytheme" to "TradeRamp"

### 3. Fix Broken Links
- [ ] Logo link points to non-existent "index-2.html"
- [ ] Update to: `<a class="logo" href="/">`

### 4. Security Updates
- [ ] Update Content-Security-Policy in nginx.conf
  - Remove `'unsafe-inline'` and `'unsafe-eval'`
  - Use nonces or hashes for inline scripts
- [ ] Add rate limiting to nginx
- [ ] Implement proper HTTPS redirect

## ⚠️ Important Updates

### 5. Legal/Compliance
- [ ] Create and link Privacy Policy page
- [ ] Create and link Terms of Service page
- [ ] Add cookie consent banner (if using analytics)
- [ ] Update copyright year dynamically

### 6. Contact Information
- [ ] Add real phone number
- [ ] Add real email address
- [ ] Add physical address (if required)
- [ ] Add business hours

### 7. Images and Content
- [ ] Replace stock testimonial photos (1.jpg, 4.jpg)
- [ ] Add real project portfolio images
- [ ] Ensure all images have proper licensing
- [ ] Add alt text to all images for accessibility

### 8. Analytics and Tracking
- [ ] Set up Google Analytics 4 properly
- [ ] Configure Facebook Pixel (if needed)
- [ ] Add conversion tracking for form submissions
- [ ] Test all tracking in production

## 🎯 Performance Optimizations

### 9. Asset Optimization
- [ ] Minify all CSS and JavaScript
- [ ] Remove unused CSS rules
- [ ] Optimize images (WebP format)
- [ ] Enable gzip compression (already in nginx)
- [ ] Set up CDN for static assets

### 10. Code Cleanup
- [ ] Remove unused JavaScript libraries
- [ ] Remove commented-out code
- [ ] Consolidate duplicate CSS rules
- [ ] Remove template-specific classes not used

## 📋 Configuration Tasks

### 11. Environment Configuration
- [ ] Set up environment variables for:
  - API endpoints
  - Analytics IDs
  - Email service keys
  - Domain names
- [ ] Create .env.example file
- [ ] Document all required environment variables

### 12. Infrastructure Setup
- [ ] Configure Route 53 DNS records
- [ ] Set up SSL certificate in ACM
- [ ] Configure CloudWatch alarms
- [ ] Set up backup strategy
- [ ] Configure WAF rules (optional)

### 13. Email Configuration
- [ ] Set up email service (SES, SendGrid)
- [ ] Configure SPF, DKIM, DMARC records
- [ ] Create email templates for form submissions
- [ ] Set up notification emails for new leads

## 🧪 Testing Checklist

### 14. Pre-deployment Testing
- [ ] Test form submission end-to-end
- [ ] Test on mobile devices
- [ ] Test page load speed (aim for < 3 seconds)
- [ ] Test all links and buttons
- [ ] Validate HTML (W3C validator)
- [ ] Check accessibility (WAVE tool)

### 15. Security Testing
- [ ] Run security headers test
- [ ] Check for exposed sensitive data
- [ ] Test form validation bypass attempts
- [ ] Verify HTTPS everywhere
- [ ] Check for mixed content warnings

## 🚀 Deployment Steps

### 16. Final Deployment Checklist
- [ ] Update all API endpoints to production URLs
- [ ] Remove development-specific code
- [ ] Update robots.txt for production
- [ ] Create 404 error page
- [ ] Set up monitoring and alerting
- [ ] Document rollback procedure

### 17. Post-Deployment
- [ ] Verify all functionality works
- [ ] Submit sitemap to Google
- [ ] Set up uptime monitoring
- [ ] Configure backup automation
- [ ] Schedule regular security updates

## 📝 Quick Fixes Script

Here are some quick fixes you can apply:

```bash
# Fix logo link
sed -i 's|href="index-2.html"|href="/"|g' index.html

# Update meta author
sed -i 's|content="zytheme"|content="TradeRamp"|g' index.html

# Remove console.error from production
sed -i 's|console\.error|// console.error|g' assets/js/schedule-form.js

# Update copyright year
sed -i 's|2024|2025|g' index.html
```

## 🔧 Recommended Services

For quick production deployment:

1. **Form Backend**: [Formspree](https://formspree.io) or [Netlify Forms](https://www.netlify.com/products/forms/)
2. **Email Service**: [Amazon SES](https://aws.amazon.com/ses/) or [SendGrid](https://sendgrid.com)
3. **Monitoring**: [UptimeRobot](https://uptimerobot.com) or [Pingdom](https://www.pingdom.com)
4. **Analytics**: [Google Analytics 4](https://analytics.google.com)
5. **CDN**: [CloudFront](https://aws.amazon.com/cloudfront/) or [Cloudflare](https://www.cloudflare.com)

## 📊 Priority Matrix

**Do First** (Blocks deployment):
- Form backend implementation
- Fix broken links
- Remove console logs

**Do Soon** (Within first week):
- Add legal pages
- Set up analytics
- Optimize images

**Do Eventually** (Continuous improvement):
- Performance optimization
- A/B testing
- Advanced monitoring

---

**Note**: This checklist should be reviewed and updated based on your specific business requirements and compliance needs.