# HubSpot Form Integration Setup Guide

This guide explains how to configure the HubSpot form integration for TradeRamp.

## Prerequisites

1. Active HubSpot account (free or paid)
2. Access to HubSpot Forms
3. Form created in HubSpot with required fields

## Step 1: Create Your HubSpot Form

1. Log in to your HubSpot account
2. Navigate to Marketing > Lead Capture > Forms
3. Create a new form or use an existing one
4. Add the following fields (recommended):
   - First Name (required)
   - Last Name (required) 
   - Email (required)
   - Phone Number (required)
   - Company/Business Name (required)
   - Trade Type (dropdown with options: Plumbing, Electrical, HVAC, Roofing, Painting, Construction, Landscaping, Other)
   - Message/Comments (optional textarea)

## Step 2: Get Your HubSpot IDs

1. In HubSpot, go to your form settings
2. Find and copy:
   - **Portal ID**: This is your HubSpot account ID (usually 6-8 digits)
   - **Form ID**: This is the unique identifier for your form (UUID format)

## Step 3: Update the Website Configuration

### Option 1: Update HTML directly

Edit `index.html` and replace the placeholder values:

```html
<div class="hs-form-frame" 
     data-region="na2" 
     data-form-id="YOUR-HUBSPOT-FORM-ID" 
     data-portal-id="YOUR-HUBSPOT-PORTAL-ID">
```

Replace:
- `YOUR-HUBSPOT-FORM-ID` with your actual form ID
- `YOUR-HUBSPOT-PORTAL-ID` with your actual portal ID

### Option 2: Update JavaScript configuration

Edit `assets/js/hubspot-form.js` and update the config object:

```javascript
config: {
    portalId: 'YOUR-HUBSPOT-PORTAL-ID', // Replace with actual portal ID
    formId: 'YOUR-HUBSPOT-FORM-ID',     // Replace with actual form ID
    region: 'na2',
    // ... rest of config
}
```

## Step 4: Customize Form Appearance

The form styling is controlled by `assets/css/modules/hubspot-form.css`. You can modify:

- Colors to match your brand
- Font sizes and families
- Button styles
- Field spacing and layout

## Step 5: Set Up Form Notifications

In HubSpot:

1. Go to your form settings
2. Click on "Options" tab
3. Set up email notifications to alert your team when someone submits the form
4. Configure the follow-up email to the person who submitted the form

## Step 6: Test the Integration

1. Load your website locally or on a staging server
2. Navigate to the contact form section
3. Verify the form loads correctly
4. Submit a test entry
5. Check that:
   - Data appears in HubSpot
   - Notifications are sent
   - Success message displays correctly

## Step 7: Connect to Your CRM Workflow

In HubSpot:

1. Create a workflow for new form submissions
2. Set up actions like:
   - Send internal notification
   - Create a deal
   - Assign to sales rep
   - Add to email nurture sequence

## Troubleshooting

### Form not loading

1. Check browser console for errors
2. Verify Portal ID and Form ID are correct
3. Ensure HubSpot script is loading (check Network tab)
4. Make sure you're not blocking third-party scripts

### Styling issues

1. Check that `hubspot-form.css` is loading
2. Use browser inspector to identify conflicting styles
3. Add more specific CSS selectors if needed

### Submissions not working

1. Check HubSpot form settings
2. Verify all required fields are present
3. Check for JavaScript errors
4. Test in incognito mode to rule out browser extensions

## Advanced Configuration

### Custom Success Message

Update the success message in `hubspot-form.js`:

```javascript
inlineMessage: 'Thank you! We\'ll contact you within 24 hours.',
```

### Add Custom Fields

If you need additional fields:

1. Add them in HubSpot form builder
2. They will automatically appear in the embedded form
3. Style them using the `.hs-form-field` classes in CSS

### Analytics Tracking

The integration automatically tracks:
- Form views
- Form submissions
- Field interactions

Events are sent to:
- Google Analytics (if configured)
- Facebook Pixel (if configured)

## Security Considerations

1. HubSpot forms include built-in spam protection
2. Enable CAPTCHA in HubSpot form settings if needed
3. Set up form submission limits if experiencing abuse
4. Review submissions regularly for quality

## Support

For HubSpot-specific issues:
- HubSpot Support: https://help.hubspot.com/
- HubSpot Community: https://community.hubspot.com/

For website integration issues:
- Check browser console for errors
- Review this documentation
- Contact your web developer