# 🔄 Update Analytics IDs in HTML Files Guide

## Overview
This guide explains how to update the placeholder analytics IDs with your actual IDs in all HTML files.

## 1. Yandex.Metrika ID Update

### Files That Need Updating:
All HTML files in the `/static/` directory that contain Yandex.Metrika code:
- `/static/index.html`
- `/static/catalog.html`
- `/static/services.html`
- `/static/calculator.html`
- `/static/reviews.html`
- `/static/portfolio.html`
- And any other HTML files with Yandex.Metrika code

### Steps to Update:

1. **Find the Placeholder ID:**
   Look for this code snippet in each HTML file:
   ```javascript
   ym(98765432, "init", {
   ```
   And also in the noscript tag:
   ```html
   <img src="https://mc.yandex.ru/watch/98765432" 
   ```

2. **Replace with Your Actual ID:**
   Replace `98765432` with your actual Yandex.Metrika Counter ID.

3. **Example Before:**
   ```javascript
   ym(98765432, "init", {
        clickmap:true,
        trackLinks:true,
        accurateTrackBounce:true,
        webvisor:true
   });
   ```
   
   **Example After (with actual ID 12345678):**
   ```javascript
   ym(12345678, "init", {
        clickmap:true,
        trackLinks:true,
        accurateTrackBounce:true,
        webvisor:true
   });
   ```

## 2. Google Analytics ID Update

### File That Needs Updating:
- `/static/index.html` (main file with Google Analytics)

### Steps to Update:

1. **Find the Placeholder ID:**
   Look for this code snippet:
   ```html
   <script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
   ```
   And also:
   ```javascript
   gtag('config', 'G-XXXXXXXXXX');
   ```

2. **Replace with Your Actual ID:**
   Replace `G-XXXXXXXXXX` with your actual Google Analytics Measurement ID.

3. **Example Before:**
   ```html
   <script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
   <script>
     window.dataLayer = window.dataLayer || [];
     function gtag(){dataLayer.push(arguments);}
     gtag('js', new Date());
     gtag('config', 'G-XXXXXXXXXX');
   </script>
   ```
   
   **Example After (with actual ID G-ABC123DEF4):**
   ```html
   <script async src="https://www.googletagmanager.com/gtag/js?id=G-ABC123DEF4"></script>
   <script>
     window.dataLayer = window.dataLayer || [];
     function gtag(){dataLayer.push(arguments);}
     gtag('js', new Date());
     gtag('config', 'G-ABC123DEF4');
   </script>
   ```

## 3. Search and Replace Method

### Using a Code Editor (VS Code, Sublime Text, etc.):

1. Open the entire `/static/` folder in your editor
2. Use Find and Replace (Ctrl+Shift+H or Cmd+Shift+H)
3. Search for: `98765432` 
   Replace with: `YOUR_YANDEX_ID`
4. Search for: `G-XXXXXXXXXX`
   Replace with: `YOUR_GOOGLE_ANALYTICS_ID`
5. Make sure to enable "Replace in Files" or similar option

### Manual Method:

1. Open each HTML file one by one
2. Search for the placeholder IDs
3. Replace with actual IDs
4. Save each file

## 4. Verification Checklist

After updating all files:

- [ ] All HTML files have been checked
- [ ] Yandex.Metrika ID updated in all files
- [ ] Google Analytics ID updated in index.html
- [ ] No placeholder IDs remain
- [ ] Syntax is correct (no broken JavaScript)
- [ ] Files saved properly

## 5. Testing the Updates

1. **Local Testing:**
   - Open each HTML file in a browser
   - Check browser console for JavaScript errors
   - Verify the analytics scripts load without errors

2. **Network Tab Check:**
   - Open Developer Tools (F12)
   - Go to Network tab
   - Refresh the page
   - Look for requests to:
     - `mc.yandex.ru` (Yandex.Metrika)
     - `googletagmanager.com` (Google Analytics)

3. **Real-Time Monitoring:**
   - Visit your site
   - Check real-time reports in both analytics platforms
   - Confirm visits are being recorded

## 6. Common Issues and Solutions

### Issue: Wrong ID Format
**Symptoms:** Analytics not recording data
**Solution:** 
- Yandex.Metrika ID should be numeric (e.g., 12345678)
- Google Analytics ID should start with "G-" (e.g., G-ABC123DEF4)

### Issue: JavaScript Errors
**Symptoms:** Console errors, page not loading properly
**Solution:**
- Check that all parentheses and brackets are properly closed
- Verify there are no extra spaces in the ID
- Ensure the script tags are properly formatted

### Issue: Missing Updates
**Symptoms:** Some pages not tracking
**Solution:**
- Double-check all HTML files
- Use search functionality to ensure no placeholders remain
- Verify all files have been saved

## 7. Backup Recommendation

Before making changes:
1. Create a backup of all HTML files
2. Or use Git to commit current state:
   ```bash
   git add .
   git commit -m "Backup before analytics ID update"
   ```

## 8. Post-Update Actions

After updating all IDs:
1. Deploy the updated files to your server
2. Test tracking on the live site
3. Set up goals/events in your analytics platforms
4. Monitor data flow for the first 24-48 hours