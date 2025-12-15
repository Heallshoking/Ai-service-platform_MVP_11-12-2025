#!/usr/bin/env python3
"""Простой деплой бота через subprocess"""
import subprocess
import sys

VPS = "176.98.178.109"
PASSWORD = "pneDRE2K?Tz1k-"

def run_ssh_command(command):
    """Выполнить SSH команду"""
    full_cmd = f'sshpass -p "{PASSWORD}" ssh -o StrictHostKeyChecking=no root@{VPS} "{command}"'
    try:
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"

def copy_file(local, remote):
    """Копировать файл через SCP"""
    cmd = f'sshpass -p "{PASSWORD}" scp -o StrictHostKeyChecking=no {local} root@{VPS}:{remote}'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode == 0

print("\n🚀 Деплой Telegram бота @Baltset39_bot\n")

# Проверяем sshpass
print("🔍 Проверка sshpass...")
check = subprocess.run("which sshpass", shell=True, capture_output=True)
if check.returncode != 0:
    print("❌ sshpass не установлен")
    print("💡 Установите: brew install hudochenkov/sshpass/sshpass")
    print("\nИЛИ используйте ручной метод:")
    print(f"  scp telegram_lead_bot.py root@{VPS}:/root/")
    print(f"  ssh root@{VPS}")
    print("  cd /root && mkdir -p baltset_bot && mv telegram_lead_bot.py baltset_bot/")
    print("  apt update && apt install -y python3-pip")
    print("  pip3 install python-telegram-bot==13.15")
    print("  python3 baltset_bot/telegram_lead_bot.py &")
    sys.exit(1)

print("✅ sshpass найден\n")

# Копируем файлы
print("📦 Копирование файлов...")
if copy_file("telegram_lead_bot.py", "/root/"):
    print("  ✅ telegram_lead_bot.py")
else:
    print("  ❌ Ошибка копирования telegram_lead_bot.py")
    sys.exit(1)

if copy_file(".env", "/root/"):
    print("  ✅ .env")
else:
    print("  ❌ Ошибка копирования .env")

print("\n⚙️  Настройка...")

# Команды настройки
commands = [
    ("Создание директории", "mkdir -p /root/baltset_bot"),
    ("Перемещение файлов", "mv /root/telegram_lead_bot.py /root/baltset_bot/ 2>/dev/null || true; mv /root/.env /root/baltset_bot/ 2>/dev/null || true"),
    ("Установка Python", "apt-get update -qq && apt-get install -y python3 python3-pip -qq"),
    ("Установка библиотек", "pip3 install python-telegram-bot==13.15 -q"),
    ("Остановка старого", "pkill -f telegram_lead_bot.py || true; systemctl stop baltset-bot 2>/dev/null || true"),
]

for desc, cmd in commands:
    print(f"  {desc}...", end=" ", flush=True)
    success, stdout, stderr = run_ssh_command(cmd)
    if success or "|| true" in cmd:
        print("✅")
    else:
        print(f"❌ {stderr[:50]}")

# Создаём systemd сервис
print("  Создание сервиса...", end=" ", flush=True)
service = """[Unit]
Description=BALTSET Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=/root/baltset_bot
ExecStart=/usr/bin/python3 /root/baltset_bot/telegram_lead_bot.py
Restart=always

[Install]
WantedBy=multi-user.target"""

service_cmd = f"echo '{service}' > /etc/systemd/system/baltset-bot.service"
run_ssh_command(service_cmd)
print("✅")

# Запуск
print("\n🚀 Запуск бота...")
run_ssh_command("systemctl daemon-reload")
run_ssh_command("systemctl start baltset-bot")
run_ssh_command("systemctl enable baltset-bot")

import time
time.sleep(2)

# Проверка
success, status, _ = run_ssh_command("systemctl is-active baltset-bot")
if success and "active" in status:
    print("\n" + "="*50)
    print("✅ БОТ ЗАПУЩЕН!")
    print("="*50)
    print("\n📱 https://t.me/Baltset39_bot")
    print("💬 Напишите /start")
    
    _, logs, _ = run_ssh_command("journalctl -u baltset-bot -n 5 --no-pager")
    print("\n📋 Логи:")
    print(logs)
else:
    print("\n❌ Ошибка запуска")
    _, logs, _ = run_ssh_command("journalctl -u baltset-bot -n 20 --no-pager")
    print(logs)

print("\n🎉 Готово!\n")
