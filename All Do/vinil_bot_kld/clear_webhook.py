#!/usr/bin/env python3
"""
Утилита для очистки webhook и pending updates
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN не найден в .env")
    exit(1)

print("🔧 Очистка webhook и pending updates...")
r = requests.post(
    f'https://api.telegram.org/bot{TOKEN}/deleteWebhook',
    json={'drop_pending_updates': True}
)
print(f"deleteWebhook: {r.json()}")

print("\n📋 Информация о webhook:")
r = requests.get(f'https://api.telegram.org/bot{TOKEN}/getWebhookInfo')
info = r.json()
if info['ok']:
    webhook = info['result']
    print(f"  URL: {webhook.get('url', '(не установлен)')}")
    print(f"  Pending updates: {webhook.get('pending_update_count', 0)}")
    print(f"  Last error: {webhook.get('last_error_message', '(нет ошибок)')}")
else:
    print(f"  ❌ Ошибка: {info}")

print("\n✅ Готово! Теперь можно перезапустить сервис:")
print("   sudo systemctl restart vinyl_bot.service")
