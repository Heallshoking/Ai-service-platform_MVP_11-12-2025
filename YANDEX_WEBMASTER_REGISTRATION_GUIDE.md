# 🕸️ Yandex.Webmaster Registration Guide

## Overview
This guide explains how to register your website in Yandex.Webmaster, confirm ownership, and submit your sitemap for indexing.

## Prerequisites
- A Yandex account (create one at https://passport.yandex.ru if needed)
- Your website URL: `https://app.balt-set.ru`
- Access to your website files (for verification)

## Step-by-Step Registration Process

### 1. Access Yandex.Webmaster
1. Go to https://webmaster.yandex.ru
2. Sign in with your Yandex account
3. If you don't have an account, create one first

### 2. Add Your Website
1. Click "Добавить сайт" (Add site)
2. Enter your website URL: `https://app.balt-set.ru`
3. Click "Добавить сайт" (Add site)

### 3. Confirm Ownership
Yandex offers several methods to confirm you own the website:

#### Method 1: HTML File (Recommended)
1. Download the verification file provided by Yandex
2. Upload it to your website's root directory (`/static/`)
3. Ensure it's accessible at `https://app.balt-set.ru/filename.html`
4. Click "Проверить" (Check) in Yandex.Webmaster

#### Method 2: Meta Tag
1. Copy the meta tag provided by Yandex
2. Add it to the `<head>` section of your main HTML file (`/static/index.html`)
3. Example:
```html
<meta name="yandex-verification" content="your_verification_code_here" />
```
4. Save and upload the file
5. Click "Проверить" (Check) in Yandex.Webmaster

#### Method 3: DNS Record
1. Add a TXT record to your domain's DNS settings
2. Use the values provided by Yandex
3. Wait for DNS propagation (may take several minutes to hours)
4. Click "Проверить" (Check) in Yandex.Webmaster

#### Method 4: HTML Content
1. Add the provided text to your main page's visible content
2. This method is not recommended as it affects user experience

### 4. Complete Initial Setup
After confirming ownership:
1. Review the site information Yandex has detected
2. Check that all pages are accessible
3. Verify robots.txt is properly configured
4. Confirm sitemap location (we'll add this in a later step)

## Site Verification Process

### Checking Indexing Status
1. In Yandex.Webmaster dashboard, select your site
2. Go to "Индексирование" (Indexing) > "Страницы в поиске" (Pages in search)
3. View indexed pages and any crawl errors

### Submitting Pages for Reindexing
1. If you've made changes, you can request reindexing
2. Go to "Индексирование" (Indexing) > "Переиндексация" (Reindexing)
3. Enter URLs you want to be reindexed
4. Submit the request

## Sitemap Submission

### Adding Your Sitemap
1. In Yandex.Webmaster, go to "Индексирование" (Indexing) > "Sitemap-файлы" (Sitemap files)
2. Click "Добавить Sitemap" (Add Sitemap)
3. Enter your sitemap URL: `https://app.balt-set.ru/sitemap.xml`
4. Click "Добавить" (Add)

### Monitoring Sitemap Processing
1. Check the status of your sitemap submission
2. View any errors or warnings
3. Monitor how many URLs have been indexed

## Essential Settings to Configure

### Robots.txt Checker
1. Go to "Индексирование" (Indexing) > "robots.txt"
2. Review any issues with your robots.txt file
3. Fix any problems that prevent proper crawling

### Internal Links Analysis
1. Go to "Индексирование" (Indexing) > "Внутренние ссылки" (Internal links)
2. Analyze your site's link structure
3. Identify and fix broken links

### Excluded Pages
1. Review pages excluded from indexing
2. Check "Индексирование" (Indexing) > "Исключённые страницы" (Excluded pages)
3. Remove exclusion reasons if appropriate

## Turbo Pages (Optional)
Yandex offers Turbo Pages for faster mobile loading:

### Enabling Turbo Pages
1. Go to "Турбо-страницы" (Turbo pages)
2. Review the requirements
3. Enable if your content meets criteria
4. Monitor performance improvements

## Search Query Analytics

### Viewing Search Statistics
1. Go to "Поисковые запросы" (Search queries)
2. View which queries bring traffic to your site
3. Analyze click-through rates and positions

### Position Tracking
1. Monitor your rankings for important keywords
2. Set up alerts for ranking changes
3. Compare performance over time

## Mobile Friendliness

### Mobile Usability Report
1. Go to "Мобильность" (Mobility)
2. Check for mobile usability issues
3. Fix any problems affecting mobile users

## Security Monitoring

### Security Issues
1. Go to "Безопасность" (Security)
2. Check for malware or hacking attempts
3. Address any security warnings promptly

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

## Best Practices

### Regular Monitoring
- Check Yandex.Webmaster weekly for new issues
- Monitor indexing status after content updates
- Review search query performance monthly

### Proactive Optimization
- Fix crawl errors promptly
- Submit new content for indexing
- Update sitemap when adding new pages

### Performance Tracking
- Monitor site loading speed
- Track mobile usability
- Analyze user behavior data

## Checklist

- [ ] Registered at Yandex.Webmaster
- [ ] Added website URL: https://app.balt-set.ru
- [ ] Confirmed ownership using preferred method
- [ ] Reviewed initial site information
- [ ] Checked robots.txt for issues
- [ ] Submitted sitemap.xml
- [ ] Monitored indexing status
- [ ] Set up search query tracking
- [ ] Configured mobile usability monitoring
- [ ] Enabled security monitoring

## Additional Resources

- Yandex.Webmaster Help: https://yandex.ru/support/webmaster/
- Yandex.Webmaster Blog: https://webmaster.yandex.ru/blog/
- Technical Support: https://yandex.ru/support/webmaster/troubleshooting/

## Security Considerations

- Keep your Yandex account secure with 2FA
- Regularly review site access permissions
- Monitor for unauthorized changes
- Respond to security alerts immediately