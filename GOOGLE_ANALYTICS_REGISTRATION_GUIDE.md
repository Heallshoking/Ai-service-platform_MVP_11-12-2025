# 📈 Google Analytics Registration Guide

## Overview
This guide explains how to register for Google Analytics and obtain your Measurement ID for website tracking.

## Prerequisites
- A Google account (Gmail or Google Workspace)
- Access to your website files
- Basic understanding of HTML

## Step-by-Step Registration Process

### 1. Access Google Analytics
1. Go to https://analytics.google.com
2. Sign in with your Google account
3. If you're new to Google Analytics, you'll see a welcome screen

### 2. Create an Account
1. Click "Start measuring" or "Admin" (gear icon in bottom left)
2. In the ACCOUNT column, click "Create Account"
3. Enter an account name (e.g., "BALTSET Electric Services")

### 3. Set Up Property
1. In the PROPERTY setup section:
   - Property name: "BALTSET Website"
   - Reporting timezone: Europe/Kaliningrad
   - Currency: Russian Ruble (RUB)
2. Select "Show advanced options"
3. Enable "Create a Universal Analytics property" if needed (optional)

### 4. Configure Property Details
1. Select "Web" as platform
2. Enter your website URL: `https://app.balt-set.ru`
3. Enter a name for your stream (e.g., "Main Website Stream")
4. Click "Create"

### 5. Obtain Your Measurement ID
1. After successful creation, you'll see your Measurement ID
2. It will look like: `G-ABC123DEF4`
3. Copy this ID for use in your website code

### 6. Get Tracking Code
1. On the same page, you'll see the Global Site Tag (gtag.js) code
2. This is the code you need to add to your website
3. The code looks like this:
```html
<!-- Global site tag (gtag.js) - Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=YOUR_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'YOUR_MEASUREMENT_ID');
</script>
```

## Implementation Instructions

### Adding Code to Your Website
1. Open `/static/index.html` in a text editor
2. Paste the Google Analytics code in the `<head>` section
3. Replace `YOUR_MEASUREMENT_ID` with your actual ID
4. Save the file

### Example Implementation:
```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>БАЛТСЕТЬ - Услуги электрика в Калининграде</title>
    
    <!-- Global site tag (gtag.js) - Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-ABC123DEF4"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());

      gtag('config', 'G-ABC123DEF4');
    </script>
    
    <!-- Other head elements -->
</head>
<body>
    <!-- Website content -->
</body>
</html>
```

## Verification Process

### Real-Time Reports
1. Visit your website in a browser
2. Go back to Google Analytics
3. Navigate to Reports > Real-time > Overview
4. You should see active users if tracking is working

### Debugging Tools
1. Install Google Analytics Debugger extension for Chrome
2. Enable it and refresh your website
3. Check the browser console for tracking information

### Google Tag Assistant (Legacy)
1. Install Google Tag Assistant extension
2. Record a session while visiting your site
3. Check for proper tag firing

## Advanced Configuration Options

### Enhanced Measurement
Enable additional automatic tracking:
- Scrolling
- Outbound clicks
- Site search
- Video engagement
- File downloads

### Event Tracking
Set up custom events for important actions:
```javascript
// Track button clicks
gtag('event', 'click', {
  'event_category': 'engagement',
  'event_label': 'order-button'
});
```

### E-commerce Tracking
If you have an online store:
1. Enable Ecommerce in Admin > Property > Ecommerce Settings
2. Implement purchase tracking code

## Data Streams Management

### View Existing Streams
1. Go to Admin > Property > Data Streams
2. See all configured streams
3. Edit stream settings if needed

### Add Additional Streams
For tracking multiple platforms:
1. iOS app
2. Android app
3. Additional websites

## User Management and Permissions

### Add Team Members
1. Go to Admin > Account > Account User Access
2. Click "Add" and enter email addresses
3. Set appropriate permissions:
   - Read & Analyze
   - Edit
   - Collaborate
   - Manage Users

### Property-Level Permissions
1. Admin > Property > Property User Access
2. Control access to specific properties
3. Useful for agencies managing multiple clients

## Troubleshooting Common Issues

### Issue: Data Not Appearing
**Solutions:**
- Wait 24-48 hours for initial data processing
- Check that the code is placed correctly in `<head>`
- Verify the Measurement ID is correct
- Check for JavaScript errors in browser console

### Issue: Incorrect Tracking
**Solutions:**
- Ensure only one Analytics tag is installed
- Check for conflicting tags from plugins or CMS
- Verify domain settings in property configuration

### Issue: Missing Events
**Solutions:**
- Check event implementation code
- Verify event names and parameters
- Use Google Tag Manager debug mode

## Best Practices

### Implementation
- Place the tracking code in the `<head>` section
- Use consistent naming conventions
- Implement event tracking for key user actions
- Set up goals for conversion tracking

### Data Quality
- Use filters to exclude internal traffic
- Set up cross-domain tracking if needed
- Implement UTM parameter tracking for campaigns
- Regular audit of tracking implementation

## Checklist

- [ ] Registered for Google Analytics account
- [ ] Created property for website
- [ ] Obtained Measurement ID
- [ ] Added tracking code to index.html
- [ ] Verified tracking is working
- [ ] Configured enhanced measurement options
- [ ] Set up basic goals/events
- [ ] Added team members with appropriate permissions
- [ ] Tested on multiple devices/browsers

## Additional Resources

- Google Analytics Help Center: https://support.google.com/analytics
- Google Analytics Academy: https://analytics.google.com/analytics/academy/
- Google Analytics Demo Account: https://ga-demo.appspot.com/

## Security Considerations

- Keep your Measurement ID private but not secret (it's visible in client-side code)
- Use Google Analytics Terms of Service compliant methods
- Consider GDPR/privacy compliance for European visitors
- Regular review of user access permissions