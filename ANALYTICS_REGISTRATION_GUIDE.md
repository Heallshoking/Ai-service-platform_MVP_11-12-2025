# 📊 Analytics Services Registration Guide

## Overview
This guide explains how to register for and configure analytics services for your website.

## 1. Яндекс.Метрика Registration

### Step-by-Step Process:
1. Go to https://metrika.yandex.ru
2. Click "Добавить счётчик" (Add Counter)
3. Enter your site information:
   - Site URL: `https://app.balt-set.ru`
   - Site name: `БАЛТСЕТЬ - Услуги электрика в Калининграде`
4. Select "Код для всех страниц сайта" (Code for all site pages)
5. Copy your Counter ID (it will look like: 95847362)

### Counter ID Usage:
After obtaining your ID, you need to replace the placeholder `98765432` in all HTML files with your actual ID.

Files that need updating:
- `/static/index.html`
- `/static/catalog.html`
- `/static/services.html`
- `/static/calculator.html`
- And any other HTML files with Yandex.Metrika code

## 2. Google Analytics Registration

### Step-by-Step Process:
1. Go to https://analytics.google.com
2. Create an account if you don't have one
3. Click "Admin" (gear icon) in the lower left
4. In the "Property" column, click "Create Property"
5. Enter property details:
   - Property name: `БАЛТСЕТЬ`
   - Reporting timezone: `Europe/Kaliningrad`
   - Currency: `Russian Ruble (RUB)`
6. Select "Web" as platform
7. Enter your website URL: `https://app.balt-set.ru`
8. Click "Create"

### Measurement ID:
After setup, you'll receive a Measurement ID (it will look like: G-ABC123DEF4)

Replace the placeholder `G-XXXXXXXXXX` in `/static/index.html` with your actual ID.

## 3. Implementation Notes

### Yandex.Metrika Code Block:
```javascript
<!-- Yandex.Metrika counter -->
<script type="text/javascript" >
   (function(m,e,t,r,i,k,a){m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
   m[i].l=1*new Date();
   for (var j = 0; j < document.scripts.length; j++) {if (document.scripts[j].src === r) { return; }}
   k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)})
   (window, document, "script", "https://mc.yandex.ru/metrika/tag.js", "ym");

   ym(YOUR_ACTUAL_ID, "init", {
        clickmap:true,
        trackLinks:true,
        accurateTrackBounce:true,
        webvisor:true
   });
</script>
<noscript><div><img src="https://mc.yandex.ru/watch/YOUR_ACTUAL_ID" style="position:absolute; left:-9999px;" alt="" /></div></noscript>
<!-- /Yandex.Metrika counter -->
```

### Google Analytics Code Block:
```javascript
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=YOUR_ACTUAL_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'YOUR_ACTUAL_ID');
</script>
<!-- /Google Analytics -->
```

## 4. Verification

### Yandex.Metрика Verification:
1. After implementing the code, visit your site
2. Go to your Yandex.Metrika dashboard
3. Check the "Real-time" report to see visits
4. Wait 24-48 hours for full data processing

### Google Analytics Verification:
1. After implementing the code, visit your site
2. Go to Google Analytics Real-time reports
3. You should see active users
4. Check the "DebugView" in GA4 for detailed event tracking

## 5. Goals Setup (Optional but Recommended)

### Yandex.Metrika Goals:
1. In your counter settings, go to "Goals"
2. Add goals for:
   - Form submissions
   - Phone calls
   - Service selections
   - Page views

### Google Analytics Events:
1. Set up events for:
   - Button clicks
   - Form interactions
   - Service selections
   - Calculator usage

## 6. Common Issues and Solutions

### Issue: Counter not recording data
**Solution:** 
- Check that the code is placed correctly before `</head>`
- Ensure there are no JavaScript errors
- Verify the Counter ID is correct

### Issue: Delayed data appearance
**Solution:** 
- Normal processing time is 24-48 hours
- Real-time data should appear immediately
- Check filters and exclusions

## 7. Security Considerations

- Keep your Counter IDs private
- Don't expose them in public documentation
- Use environment variables in production if possible
- Regularly review access permissions

## 8. Checklist

- [ ] Registered in Yandex.Metrika
- [ ] Obtained Yandex Counter ID
- [ ] Registered in Google Analytics
- [ ] Obtained Google Measurement ID
- [ ] Updated all HTML files with Yandex ID
- [ ] Updated index.html with Google ID
- [ ] Verified tracking is working
- [ ] Set up basic goals/events
- [ ] Tested on multiple pages