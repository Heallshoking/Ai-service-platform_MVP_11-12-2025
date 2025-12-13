# 🚀 Quick Start: Deploy Telegram Bots to VPS (5 minutes)

## 📋 Server Information

- **VPS IP:** `176.98.178.109`
- **SSH Login:** `root@176.98.178.109`
- **Password:** `pneDRE2K?Tz1k-`

---

## ⚡ Step 1: Connect to VPS & Deploy (2 minutes)

Open your terminal and run these commands:

```bash
# 1. Connect to VPS
ssh root@176.98.178.109
# When prompted, enter password: pneDRE2K?Tz1k-

# 2. Download setup script
curl -o setup_vps.sh https://raw.githubusercontent.com/Heallshoking/balt-set.ru/main/setup_vps.sh

# 3. Make it executable
chmod +x setup_vps.sh

# 4. Run installation
./setup_vps.sh
```

**What the script does:**
- ✅ Updates system packages
- ✅ Installs Python 3.11
- ✅ Creates secure user `botuser`
- ✅ Clones project from GitHub
- ✅ Installs dependencies
- ✅ Creates `.env` with bot tokens
- ✅ Sets up systemd services for 24/7 operation
- ✅ Starts both bots

**Installation time: ~5 minutes**

---

## ✅ Step 2: Testing (3 minutes)

### Test the bots on Telegram:

1. **AI Chat on Website:**
   - Open: https://app.balt-set.ru

2. **Client Bot:**
   - Open Telegram: [@ai_service_client_bot](https://t.me/ai_service_client_bot)
   - Send `/start`
   - Fill in the order form (name, phone, problem, address)

3. **Master Bot:**
   - Open Telegram: [@ai_service_master_bot](https://t.me/ai_service_master_bot)
   - Send `/start`
   - Register as a master (first time)
   - Accept orders from clients

4. **Calculator:**
   - Open: https://app.balt-set.ru/calculator

---

## 👥 Step 3: Register First Master

1. Open [@ai_service_master_bot](https://t.me/ai_service_master_bot)
2. Send `/start`
3. Click "✅ Зарегистрироваться"
4. Fill in:
   - **Full Name:** (e.g., "Иван Иванов")
   - **Phone:** (e.g., "+79001234567")
   - **City:** (e.g., "Калининград")
   - **Specializations:** Select from:
     - ⚡ Электрика
     - 🚰 Сантехника
     - 🔌 Бытовая техника
     - 🔨 Общие работы
5. Click "✅ Выбрал всё" when done
6. Confirm registration

**Your master is now ready to accept orders!** 🎉

---

## 📊 Manage Bots on VPS

### Check Status:
```bash
systemctl status telegram-client-bot telegram-master-bot
```

### View Logs (real-time):
```bash
# Client bot logs
tail -f /var/log/telegram-client-bot.log

# Master bot logs
tail -f /var/log/telegram-master-bot.log
```

### Restart Bots:
```bash
systemctl restart telegram-client-bot telegram-master-bot
```

### Stop Bots:
```bash
systemctl stop telegram-client-bot telegram-master-bot
```

### Update Code from GitHub:
```bash
cd /opt/ai-service-bots
sudo -u botuser git pull origin main
systemctl restart telegram-client-bot telegram-master-bot
```

---

## 🔍 Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'telegram'"
**Solution:**
```bash
cd /opt/ai-service-bots
sudo -u botuser venv/bin/pip install -r requirements.txt
systemctl restart telegram-client-bot telegram-master-bot
```

### Problem: "Conflict: terminated by other getUpdates request"
**Solution:** Stop local bots if running:
```bash
# On local machine
./stop_bots.sh
# or
pkill -f telegram_client_bot
pkill -f telegram_master_bot
```

### Problem: Bots not starting
**Solution:** Check logs:
```bash
journalctl -u telegram-client-bot -n 50
journalctl -u telegram-master-bot -n 50
```

---

## 📝 Architecture Overview

```
┌─────────────────────────────────────────────┐
│ Timeweb App Platform (app.balt-set.ru)     │
│ ✅ FastAPI Backend API                      │
│ ✅ Frontend (React/HTML)                    │
│ ✅ Database                                 │
│ ✅ Auto-deploy from GitHub                 │
└─────────────────────────────────────────────┘
                    ▲
                    │ HTTPS API Calls
                    │
┌─────────────────────────────────────────────┐
│ VPS Server (176.98.178.109)                │
│ ✅ Telegram Client Bot (24/7)              │
│ ✅ Telegram Master Bot (24/7)              │
│ ✅ Systemd auto-restart                    │
│ ✅ Independent operation                   │
└─────────────────────────────────────────────┘
```

---

## 🎯 Bot Configuration

### Environment Variables (`.env` on VPS):

```env
ENVIRONMENT=production
DEBUG=false
API_URL=https://app.balt-set.ru

TELEGRAM_CLIENT_BOT_TOKEN=8546494378:AAEXpAgazUGMSXi282M56uhnLBD7fwQ3UzU
TELEGRAM_MASTER_BOT_TOKEN=8558486884:AAFEAnfaAKlQtoQ0Qs9vAuJ9p0Pa-XLMsBg

PLATFORM_COMMISSION_PERCENT=25
SECRET_KEY=ai_service_platform_secret_production_2024
```

---

## ✅ Post-Installation Checklist

- [ ] Bots are running: `systemctl status telegram-client-bot telegram-master-bot`
- [ ] No errors in logs: `tail /var/log/telegram-client-bot.log`
- [ ] Client bot responds: [@ai_service_client_bot](https://t.me/ai_service_client_bot) → `/start`
- [ ] Master bot responds: [@ai_service_master_bot](https://t.me/ai_service_master_bot) → `/start`
- [ ] Auto-start enabled: `systemctl is-enabled telegram-client-bot`
- [ ] Local bots stopped: `./stop_bots.sh` (if you had them running locally)

---

## 🎉 You're Ready!

**Your Telegram bots are now running 24/7 on VPS!**

### Next Steps:

1. **Register at least 3-5 masters** through [@ai_service_master_bot](https://t.me/ai_service_master_bot)
2. **Test the flow:**
   - Create order via client bot
   - Master accepts order
   - Master updates status
   - Master completes order
3. **Share client bot** with customers
4. **Monitor logs** periodically to ensure everything works

---

## 📞 Support

If you encounter any issues:
1. Check logs: `tail -f /var/log/telegram-client-bot.log`
2. Restart bots: `systemctl restart telegram-client-bot telegram-master-bot`
3. Check API status: https://app.balt-set.ru
4. Review this guide: [VPS_DEPLOYMENT_GUIDE.md](./VPS_DEPLOYMENT_GUIDE.md)

**Good luck! 🚀**
