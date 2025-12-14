# 🗺️ Yandex Sitemap Submission Guide

## Overview
This guide explains how to submit your sitemap.xml file to Yandex.Webmaster for better indexing of your website.

## Prerequisites
- Registered website in Yandex.Webmaster
- Confirmed ownership of your site
- Valid sitemap.xml file at `https://app.balt-set.ru/sitemap.xml`

## Step-by-Step Sitemap Submission

### 1. Access Yandex.Webmaster
1. Go to https://webmaster.yandex.ru
2. Sign in with your Yandex account
3. Select your website from the dashboard

### 2. Navigate to Sitemap Section
1. In the left sidebar, go to "Индексирование" (Indexing)
2. Click on "Sitemap-файлы" (Sitemap files)

### 3. Add Your Sitemap
1. Click "Добавить Sitemap" (Add Sitemap)
2. Enter your sitemap URL: `https://app.balt-set.ru/sitemap.xml`
3. Click "Добавить" (Add)

### 4. Verify Sitemap Submission
1. Yandex will automatically fetch and process your sitemap
2. Check the status in the sitemap list
3. Look for any errors or warnings

## Sitemap Requirements

### Valid XML Format
Your sitemap must be a valid XML file following the sitemap protocol:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://app.balt-set.ru/</loc>
    <lastmod>2024-12-14</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <!-- More URLs -->
</urlset>
```

### Accessibility
- The sitemap must be publicly accessible
- No authentication required
- Proper HTTP response (200 OK)

### Size Limitations
- Maximum file size: 50 MB
- Maximum URLs per sitemap: 50,000
- For larger sites, use sitemap index files

## Monitoring Sitemap Processing

### Processing Status
1. **Не обработан** (Not processed) - Newly submitted
2. **Обрабатывается** (Processing) - Being analyzed
3. **Обработан** (Processed) - Successfully analyzed
4. **Ошибка** (Error) - Processing failed

### Error Types
- **404 Not Found** - Sitemap URL is incorrect
- **Invalid XML** - Syntax errors in sitemap
- **Too Large** - Exceeds size limitations
- **Server Error** - HTTP 5xx errors

## Resubmitting Sitemap

### When to Resubmit
- After adding new content
- After fixing sitemap errors
- When sitemap is updated significantly

### How to Resubmit
1. Make necessary changes to your sitemap.xml file
2. Upload the updated file to your server
3. In Yandex.Webmaster, find your sitemap
4. Click "Переобработать" (Reprocess) or delete and re-add

## Sitemap Best Practices

### Regular Updates
- Update sitemap when adding new pages
- Modify lastmod dates for updated content
- Remove URLs for deleted pages

### Priority Settings
Use priority values appropriately:
- Homepage: 1.0
- Important service pages: 0.8-0.9
- Blog posts: 0.6-0.8
- Old/archive content: 0.3-0.5

### Change Frequency
Set realistic changefreq values:
- Homepage: daily
- Service pages: weekly
- Blog posts: monthly
- Static pages: yearly

## Advanced Sitemap Features

### Multiple Sitemaps
For large sites, create separate sitemaps by content type:
- Main pages sitemap
- Blog sitemap
- Product sitemap

Then create a sitemap index:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>https://app.balt-set.ru/sitemap-main.xml</loc>
    <lastmod>2024-12-14</lastmod>
  </sitemap>
  <sitemap>
    <loc>https://app.balt-set.ru/sitemap-blog.xml</loc>
    <lastmod>2024-12-14</lastmod>
  </sitemap>
</sitemapindex>
```

### Image Sitemaps
Include images in your sitemaps:
```xml
<url>
  <loc>https://app.balt-set.ru/services/rozetki.html</loc>
  <image:image>
    <image:loc>https://app.balt-set.ru/images/rozetki.jpg</image:loc>
    <image:title>Установка розеток</image:title>
  </image:image>
</url>
```

## Troubleshooting Common Issues

### Issue: Sitemap Not Found (404)
**Solutions:**
- Verify the sitemap URL is correct
- Check that the file exists on your server
- Ensure proper file permissions
- Test accessing the URL directly in a browser

### Issue: Invalid XML Format
**Solutions:**
- Validate your XML with an online validator
- Check for unclosed tags
- Ensure proper encoding (UTF-8)
- Remove any special characters that aren't properly escaped

### Issue: Sitemap Too Large
**Solutions:**
- Split into multiple sitemaps
- Reduce number of URLs per sitemap
- Remove old/irrelevant URLs
- Use sitemap index for organization

### Issue: Server Errors (5xx)
**Solutions:**
- Check server logs for errors
- Verify server configuration
- Contact hosting provider if needed
- Temporarily reduce sitemap size

### Issue: URLs Not Indexed
**Solutions:**
- Check robots.txt for disallow rules
- Verify URLs are accessible
- Ensure content is unique and valuable
- Submit individual URLs for indexing

## Monitoring Results

### Indexed Pages
1. Go to "Индексирование" > "Страницы в поиске"
2. View how many of your sitemap URLs are indexed
3. Identify pages that haven't been indexed

### Crawl Errors
1. Check "Индексирование" > "Ошибки при обходе"
2. Fix any crawl errors affecting sitemap URLs
3. Resubmit sitemap after fixing issues

### Excluded Pages
1. Review "Индексирование" > "Исключённые страницы"
2. Understand why pages were excluded
3. Adjust content or metadata if appropriate

## Automation Tips

### Automatic Sitemap Generation
Consider using tools to automatically generate sitemaps:
- Static site generators (Jekyll, Hugo)
- CMS plugins (WordPress, Drupal)
- Custom scripts for dynamic content

### Scheduled Updates
Set up automated processes to:
- Regenerate sitemap regularly
- Ping search engines with updates
- Monitor for broken links

## Verification Checklist

- [ ] Sitemap is accessible at https://app.balt-set.ru/sitemap.xml
- [ ] XML format is valid
- [ ] All URLs are accessible
- [ ] File size is under 50 MB
- [ ] Number of URLs is under 50,000
- [ ] Submitted to Yandex.Webmaster
- [ ] Processing completed without errors
- [ ] Indexed pages are increasing
- [ ] No crawl errors related to sitemap

## Additional Resources

- Sitemap Protocol: https://www.sitemaps.org/protocol.html
- Yandex.Webmaster Documentation: https://yandex.ru/support/webmaster/
- XML Sitemap Validators: Various online tools available

## Security Considerations

- Don't include sensitive/administrative URLs in sitemap
- Use robots.txt to exclude private areas
- Regularly audit sitemap contents for accidental exposure
- Monitor access logs for unusual sitemap activity