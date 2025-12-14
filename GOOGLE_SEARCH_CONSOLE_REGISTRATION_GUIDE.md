# 🔍 Google Search Console Registration Guide

## Overview
This guide explains how to register your website in Google Search Console, confirm ownership, and submit your sitemap for indexing.

## Prerequisites
- A Google account (Gmail or Google Workspace)
- Your website URL: `https://app.balt-set.ru`
- Access to your website files (for verification)
- Google Analytics account (recommended but not required)

## Step-by-Step Registration Process

### 1. Access Google Search Console
1. Go to https://search.google.com/search-console
2. Sign in with your Google account
3. If you don't have an account, create one first

### 2. Add Your Website Property
1. Click "Добавить свойство" (Add Property) or the "+" button
2. Enter your website URL: `https://app.balt-set.ru`
3. Select the correct protocol (HTTPS)
4. Click "Продолжить" (Continue)

### 3. Confirm Ownership
Google offers several methods to confirm you own the website:

#### Method 1: HTML File (Recommended)
1. Download the verification file provided by Google
2. Upload it to your website's root directory (`/static/`)
3. Ensure it's accessible at `https://app.balt-set.ru/filename.html`
4. Click "Проверить" (Verify) in Google Search Console

#### Method 2: HTML Tag
1. Copy the meta tag provided by Google
2. Add it to the `<head>` section of your main HTML file (`/static/index.html`)
3. Example:
```html
<meta name="google-site-verification" content="your_verification_code_here" />
```
4. Save and upload the file
5. Click "Проверить" (Verify) in Google Search Console

#### Method 3: DNS Record
1. Add a TXT record to your domain's DNS settings
2. Use the values provided by Google
3. Wait for DNS propagation (may take several minutes to hours)
4. Click "Проверить" (Verify) in Google Search Console

#### Method 4: Google Analytics
1. If you've already added Google Analytics to your site
2. Select this option to verify through existing GA connection
3. Ensure GA is properly implemented and recording data

#### Method 5: Google Tag Manager
1. If you're using Google Tag Manager
2. Select this option for verification
3. Ensure GTM is properly implemented

### 4. Complete Initial Setup
After confirming ownership:
1. Review the property details
2. Check that all pages are accessible
3. Verify robots.txt is properly configured
4. Set up email notifications for critical issues

## Site Verification Process

### Checking Indexing Status
1. In Google Search Console dashboard, select your property
2. Go to "Отчет о страницах" (Page Report) or "Coverage"
3. View indexed pages and any crawl errors

### Submitting Pages for Indexing
1. If you've made changes, you can request indexing
2. Go to "Инструменты" (Tools) > "Инспектор URL" (URL Inspector)
3. Enter URLs you want to be indexed
4. Click "Проверить живую версию URL" (Test Live URL)
5. Then click "Запросить индексирование" (Request Indexing)

## Sitemap Submission

### Adding Your Sitemap
1. In Google Search Console, go to "Индексы" (Indexes) > "Sitemaps"
2. Click "Добавить тестовый Sitemap" (Add Test Sitemap)
3. Enter your sitemap URL: `https://app.balt-set.ru/sitemap.xml`
4. Click "Отправить" (Submit)

### Monitoring Sitemap Processing
1. Check the status of your sitemap submission
2. View any errors or warnings
3. Monitor how many URLs have been discovered and indexed

## Essential Settings to Configure

### Security Issues
1. Go to "Безопасность" (Security Issues)
2. Check for malware or hacking attempts
3. Address any security warnings promptly

### Manual Actions
1. Review "Ручные действия" (Manual Actions)
2. Check if Google has applied penalties
3. Fix issues and request review if needed

### Mobile Usability
1. Go to "Мобильность" (Mobile Usability)
2. Check for mobile usability issues
3. Fix any problems affecting mobile users

### Core Web Vitals
1. Review "Core Web Vitals" report
2. Analyze page experience metrics
3. Optimize for loading, interactivity, and visual stability

## Search Performance Monitoring

### Viewing Search Analytics
1. Go to "Производительность" (Performance)
2. View which queries bring traffic to your site
3. Analyze click-through rates, positions, and impressions

### Filtering Data
1. Filter by device type (desktop, mobile, tablet)
2. Filter by country/region
3. Filter by date range
4. Filter by specific pages or queries

## URL Inspection Tool

### Checking Individual URLs
1. Go to "Инструменты" (Tools) > "Инспектор URL" (URL Inspector)
2. Enter any URL from your site
3. Check indexing status
4. View crawl issues
5. See enhancement data (structured data, AMP, etc.)

### Live URL Testing
1. Test live versions of pages
2. See how Googlebot renders your content
3. Check for JavaScript-related issues
4. Request indexing directly

## Coverage Report

### Understanding Coverage Status
1. **Исключено** (Excluded) - Deliberately removed from index
2. **Ошибки** (Errors) - Pages Google couldn't crawl or index
3. **Предупреждения** (Warnings) - Issues that may affect indexing
4. **Допустимые элементы** (Valid Items) - Successfully indexed pages

### Fixing Crawl Errors
1. Identify the type of error (404, server error, etc.)
2. Fix the underlying issue
3. Use URL Inspection tool to verify fixes
4. Request reindexing if needed

## Enhancement Reports

### Structured Data
1. Go to "Улучшения" (Enhancements) > "Данные структуры" (Structured Data)
2. View any structured data issues
3. Fix markup errors
4. Monitor rich result performance

### AMP
1. Check Accelerated Mobile Pages status
2. Fix any AMP validation errors
3. Monitor AMP performance

## Common Issues and Solutions

### Issue: Verification Failed
**Solutions:**
- Double-check the verification file/content is uploaded correctly
- Ensure the file is publicly accessible
- Clear browser cache and try again
- Try a different verification method

### Issue: Sitemap Not Accepted
**Solutions:**
- Check that sitemap.xml is valid XML
- Ensure the sitemap is accessible at the specified URL
- Validate with an online sitemap validator
- Check for server errors (404, 500, etc.)

### Issue: Pages Not Indexed
**Solutions:**
- Check robots.txt for disallow directives
- Ensure pages are linked internally
- Submit individual URLs for indexing
- Check for canonicalization issues

### Issue: Security Warnings
**Solutions:**
- Scan your site for malware
- Check for unauthorized modifications
- Update all software/plugins
- Request security review after cleaning

## Best Practices

### Regular Monitoring
- Check Google Search Console weekly for new issues
- Monitor indexing status after content updates
- Review search performance monthly

### Proactive Optimization
- Fix crawl errors promptly
- Submit new content for indexing
- Update sitemap when adding new pages

### Performance Tracking
- Monitor Core Web Vitals
- Track mobile usability
- Analyze user behavior data

## Checklist

- [ ] Registered at Google Search Console
- [ ] Added property: https://app.balt-set.ru
- [ ] Confirmed ownership using preferred method
- [ ] Reviewed initial property information
- [ ] Checked robots.txt for issues
- [ ] Submitted sitemap.xml
- [ ] Monitored indexing status
- [ ] Set up search performance tracking
- [ ] Configured mobile usability monitoring
- [ ] Enabled security monitoring
- [ ] Set up email notifications

## Additional Resources

- Google Search Console Help: https://support.google.com/webmasters/
- Google Search Console Blog: https://webmasters.googleblog.com/
- Technical Support: https://support.google.com/webmasters/community

## Security Considerations

- Keep your Google account secure with 2FA
- Regularly review property access permissions
- Monitor for unauthorized changes
- Respond to security alerts immediately