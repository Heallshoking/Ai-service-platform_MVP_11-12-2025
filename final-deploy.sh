#!/bin/bash

# 🚀 Final Deployment Script for AI Service Platform

echo "═══════════════════════════════════════════════════════════"
echo "   🚀 FINAL DEPLOYMENT OF CONVERSION-READY WEBSITE"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Create backup of existing files
echo "🔄 Creating backup of existing files..."
cd /Users/user/Documents/Projects/Github/balt-set.ru

# Backup current HTML files
mkdir -p backups/$(date +%Y%m%d_%H%M%S)
cp static/*.html backups/$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || echo "No HTML files to backup"

echo "✅ Backup completed"

# Copy new enhanced files to main directory
echo ""
echo "📂 Deploying enhanced website files..."

# Copy the enhanced homepage
cp static/enhanced-home.html static/index.html
cp static/new-catalog.html static/catalog.html
cp static/new-services.html static/services.html
cp static/new-calculator.html static/calculator.html

echo "✅ Enhanced files deployed"

# Update sitemap
echo ""
echo "🗺️ Updating sitemap..."
cp static/sitemap-updated.xml static/sitemap.xml
echo "✅ Sitemap updated"

# Update robots.txt
echo ""
echo "🤖 Updating robots.txt..."
cp static/robots-updated.txt static/robots.txt
echo "✅ Robots.txt updated"

# Git operations
echo ""
echo "💾 Committing changes..."
git add .
git commit -m "🚀 Final deployment: Conversion-ready website with enhanced SEO, navigation, and interlinking"
git push origin main

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "   ✅ DEPLOYMENT COMPLETE!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "🌐 Website is now live with enhancements:"
echo "   • Enhanced homepage with better conversions"
echo "   • Comprehensive service catalog with SEO optimization"
echo "   • Improved navigation with excellent interlinking"
echo "   • Updated sitemap and robots.txt for better SEO"
echo ""
echo "📈 The website is now ready to generate leads and conversions!"
echo ""
echo "🔗 Live URLs:"
echo "   • https://app.balt-set.ru/ - Homepage"
echo "   • https://app.balt-set.ru/catalog.html - Service Catalog"
echo "   • https://app.balt-set.ru/services.html - Services"
echo "   • https://app.balt-set.ru/calculator.html - Calculator"
echo ""
echo "⏰ Timeweb will automatically deploy within 3-5 minutes"
echo ""