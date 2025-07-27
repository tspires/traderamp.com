# How to Find Your HubSpot Portal ID and Form ID

## Quick Steps:

### 1. Portal ID (Hub ID)
- Log in to HubSpot
- Look at your browser's URL: `https://app.hubspot.com/contacts/[PORTAL-ID]/`
- The number after `/contacts/` is your Portal ID
- Example: If URL is `https://app.hubspot.com/contacts/12345678/`, your Portal ID is `12345678`

### 2. Form ID
- Go to Marketing > Lead Capture > Forms
- Click on your form (or create a new one)
- Click "Share" or "Embed" button
- Look for the embed code - it contains both IDs
- The Form ID is a UUID format like: `a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6`

### 3. Example Embed Code
When you click "Share" on your form, you'll see code like this:
```html
<script charset="utf-8" type="text/javascript" src="//js.hsforms.net/forms/embed/v2.js"></script>
<script>
  hbspt.forms.create({
    region: "na1",
    portalId: "12345678",
    formId: "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6"
  });
</script>
```

## Where to Update:

1. **index.html** (lines 364-365):
   ```html
   data-form-id="a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6" 
   data-portal-id="12345678"
   ```

2. **assets/js/hubspot-form.js** (lines 12-13):
   ```javascript
   portalId: '12345678',
   formId: 'a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6',
   ```

## Need a HubSpot Account?
If you don't have a HubSpot account yet:
1. Go to https://www.hubspot.com/
2. Click "Get started free"
3. Create your account
4. Create a form under Marketing > Lead Capture > Forms