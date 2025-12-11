#!/bin/bash
# Deployment script for vinyl marketplace to production server

set -e  # Exit on error

SERVER="root@176.98.178.109"
REMOTE_DIR="/root/vinyl_marketplace_RU"
LOCAL_DIR="/Users/user/Documents/Проекты/vinil_bot_kld"

echo "======================================"
echo "🚀 Deploying Vinyl Marketplace"
echo "======================================"
echo ""

# Check if we're in the right directory
if [ ! -f "vinyl_bot.py" ]; then
    echo "❌ Error: Must run from project root directory"
    exit 1
fi

echo "📦 Step 1: Creating deployment package..."

# Create temporary deployment directory
DEPLOY_DIR="/tmp/vinyl_deploy_$(date +%s)"
mkdir -p "$DEPLOY_DIR"

# Copy essential files
echo "  Copying files..."
cp vinyl_bot.py "$DEPLOY_DIR/"
cp main.py "$DEPLOY_DIR/"
cp requirements.txt "$DEPLOY_DIR/"
cp migrate_sheets.py "$DEPLOY_DIR/"
cp verify_system.py "$DEPLOY_DIR/"
cp server.env "$DEPLOY_DIR/.env"
cp -r utils "$DEPLOY_DIR/"

# Copy documentation
cp README.md "$DEPLOY_DIR/" 2>/dev/null || true
cp SETUP.md "$DEPLOY_DIR/" 2>/dev/null || true
cp COMPLETION.md "$DEPLOY_DIR/" 2>/dev/null || true

echo "  ✅ Package created: $DEPLOY_DIR"
echo ""

echo "📤 Step 2: Uploading to server..."

# Create backup on server
echo "  Creating backup on server..."
ssh "$SERVER" "cd $REMOTE_DIR && [ -d backup_\$(date +%Y%m%d) ] || cp -r . backup_\$(date +%Y%m%d) 2>/dev/null || true"

# Upload files using rsync
echo "  Uploading files via rsync..."
rsync -avz --progress \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.git' \
    --exclude 'venv' \
    --exclude 'static_export' \
    --exclude 'credentials.json' \
    "$DEPLOY_DIR/" "$SERVER:$REMOTE_DIR/"

echo "  ✅ Files uploaded"
echo ""

echo "🔧 Step 3: Server setup..."

ssh "$SERVER" << 'ENDSSH'
cd /root/vinyl_marketplace_RU

echo "  Installing dependencies..."
pip3 install -r requirements.txt --quiet

echo "  Setting permissions..."
chmod +x migrate_sheets.py verify_system.py

echo "  Checking environment..."
python3 verify_system.py || echo "⚠️ Some checks failed, review output"

echo "  ✅ Server setup complete"
ENDSSH

echo ""
echo "🔄 Step 4: Restarting services..."

ssh "$SERVER" << 'ENDSSH'
# Stop existing processes
echo "  Stopping old processes..."
pkill -f "python.*vinyl_bot.py" || true
pkill -f "python.*main.py" || true
sleep 2

# Check if systemd services exist
if systemctl list-unit-files | grep -q vinyl_bot.service; then
    echo "  Restarting systemd services..."
    systemctl restart vinyl_bot.service
    systemctl restart vinyl_api.service 2>/dev/null || echo "  ⚠️ vinyl_api.service not found"
else
    echo "  Starting in background..."
    cd /root/vinyl_marketplace_RU
    nohup python3 main.py > /tmp/vinyl_api.log 2>&1 &
    nohup python3 vinyl_bot.py > /tmp/vinyl_bot.log 2>&1 &
fi

sleep 3

# Check if processes are running
if pgrep -f "python.*vinyl_bot.py" > /dev/null; then
    echo "  ✅ Vinyl bot is running"
else
    echo "  ❌ Vinyl bot failed to start"
fi

if pgrep -f "python.*main.py" > /dev/null; then
    echo "  ✅ API server is running"
else
    echo "  ❌ API server failed to start"
fi
ENDSSH

echo ""
echo "🧹 Step 5: Cleanup..."
rm -rf "$DEPLOY_DIR"
echo "  ✅ Temporary files removed"

echo ""
echo "======================================"
echo "✅ Deployment Complete!"
echo "======================================"
echo ""
echo "📝 Next steps:"
echo "1. SSH to server: ssh $SERVER"
echo "2. Run migration: cd $REMOTE_DIR && python3 migrate_sheets.py"
echo "3. Check logs:"
echo "   - Bot: tail -f /tmp/vinyl_bot.log"
echo "   - API: tail -f /tmp/vinyl_api.log"
echo ""
echo "🔍 Verify:"
echo "   ssh $SERVER 'cd $REMOTE_DIR && python3 verify_system.py'"
echo ""
