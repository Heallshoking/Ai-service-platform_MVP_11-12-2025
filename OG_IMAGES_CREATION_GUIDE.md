# 🖼️ Open Graph Images Creation Guide

## Overview
This guide explains how to create the required Open Graph images for proper social media sharing and search engine optimization.

## Required Images

### 1. og-image.jpg (для главной страницы)
- **Size:** 1200x630 pixels
- **Text:** "БАЛТСЕТЬ - Вызов мастера за 2 минуты"
- **Background:** Gradient #667eea → #764ba2
- **Icon:** ⚡
- **Prices:** "от 500₽"

### 2. og-catalog.jpg (для каталога)
- **Size:** 1200x630 pixels
- **Text:** "Каталог услуг электрика в Калининграде"
- **Services:** "Установка розеток, Замена проводки, Штробление"
- **Prices:** "от 400₽"

### 3. og-services.jpg (для страницы услуг)
- **Size:** 1200x630 pixels
- **Text:** "Профессиональный электромонтаж"
- **Discounts:** "до 25%"

## How to Create These Images

### Option 1: Using Canva (Recommended for beginners)
1. Go to https://www.canva.com
2. Create a new design with custom dimensions: 1200 x 630 px
3. Select a gradient background (#667eea → #764ba2)
4. Add text elements as specified above
5. Add relevant icons (⚡ for main page)
6. Download as JPG format

### Option 2: Using Figma (Free alternative)
1. Go to https://www.figma.com
2. Create a new file
3. Set frame size to 1200 x 630 px
4. Create gradient background
5. Add text and icons
6. Export as JPG

### Option 3: Professional Service
- Order on Kwork for 500₽
- Search for "создание og изображений"

## Image Placement
After creating the images, upload them to the `/static/` directory:
```
/static/og-image.jpg
/static/og-catalog.jpg
/static/og-services.jpg
```

## Verification
After uploading, verify the images are working by:
1. Sharing your URLs on social media platforms
2. Using Facebook Sharing Debugger: https://developers.facebook.com/tools/debug/
3. Using Twitter Card Validator: https://cards-dev.twitter.com/validator

## Best Practices
- Keep text large enough to be readable when thumbnails are small
- Use high contrast between text and background
- Include brand elements (colors, logo)
- Keep design consistent across all images
- Test on multiple platforms

## Example Layout Structure
```
[Background Gradient]
[Large Icon]     [Main Title]
                 [Subtitle/Description]
                 [Price Information]
```

## Tools Checklist
- [ ] Canva or Figma account
- [ ] Correct dimensions (1200x630)
- [ ] Brand colors (#667eea → #764ba2)
- [ ] Relevant icons
- [ ] Clear, readable text
- [ ] Export in JPG format
- [ ] Upload to /static/ directory