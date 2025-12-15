#!/usr/bin/env python3
"""Автоматический деплой бота на VPS через paramiko"""
import paramiko
import time
import sys

VPS_HOST = "176.98.178.109"
VPS_USER = "root"
VPS_PASSWORD = "pneDRE2K?Tz1k-"

def run_command(ssh, command, description=""):
    """Выполнить команду на удалённом сервере"""
    if description:
        print(f"  {description}...", end=" ", flush=True)
    
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    
    if exit_status == 0:
        if description:
            print("✅")
        return stdout.read().decode(), stderr.read().decode()
    else:
        if description:
            print("❌")
        error = stderr.read().decode()
        if error:
            print(f"    Ошибка: {error}")
        return None, error

def main():
    print("\n🚀 Деплой Telegram бота @Baltset39_bot на VPS\n")
    
    # Подключаемся к VPS
    print(f"📡 Подключение к {VPS_HOST}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD, timeout=10)
        print("✅ Подключено\n")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        sys.exit(1)
    
    # Копируем файлы через SFTP
    print("📦 Копируем файлы на VPS...")
    sftp = ssh.open_sftp()
    
    try:
        sftp.put("telegram_lead_bot.py", "/root/telegram_lead_bot.py")
        print("  ✅ telegram_lead_bot.py")
        
        sftp.put(".env", "/root/.env")
        print("  ✅ .env")
    except Exception as e:
        print(f"  ❌ Ошибка копирования: {e}")
        sys.exit(1)
    finally:
        sftp.close()
    
    print("\n⚙️  Настройка окружения:")
    
    # Создаём директорию
    run_command(ssh, "mkdir -p /root/baltset_bot", "Создаём директорию")
    run_command(ssh, "mv /root/telegram_lead_bot.py /root/baltset_bot/ 2>/dev/null || true")
    run_command(ssh, "mv /root/.env /root/baltset_bot/ 2>/dev/null || true")
    
    # Устанавливаем зависимости
    run_command(ssh, "apt-get update -qq", "Обновляем пакеты")
    run_command(ssh, "apt-get install -y python3 python3-pip -qq", "Устанавливаем Python")
    run_command(ssh, "pip3 install python-telegram-bot==13.15 -q", "Устанавливаем библиотеки")
    
    # Останавливаем старый процесс
    run_command(ssh, "systemctl stop baltset-bot 2>/dev/null || true", "Останавливаем старый процесс")
    
    # Создаём systemd сервис
    print("  Создаём systemd сервис...", end=" ", flush=True)
    service_content = """[Unit]
Description=BALTSET Telegram Lead Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/baltset_bot
ExecStart=/usr/bin/python3 /root/baltset_bot/telegram_lead_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    stdin, stdout, stderr = ssh.exec_command(
        f"cat > /etc/systemd/system/baltset-bot.service << 'EOF'\n{service_content}\nEOF"
    )
    stdout.channel.recv_exit_status()
    print("✅")
    
    # Запускаем бота
    print("\n🚀 Запуск бота:")
    run_command(ssh, "systemctl daemon-reload", "Перезагружаем systemd")
    run_command(ssh, "systemctl start baltset-bot", "Запускаем сервис")
    run_command(ssh, "systemctl enable baltset-bot", "Включаем автозапуск")
    
    # Ждём запуска
    time.sleep(3)
    
    # Проверяем статус
    print("\n📊 Проверка статуса:")
    status_out, _ = run_command(ssh, "systemctl is-active baltset-bot")
    
    if status_out and status_out.strip() == "active":
        print("\n" + "="*50)
        print("✅ БОТ УСПЕШНО ЗАПУЩЕН!")
        print("="*50)
        print("\n📱 Проверьте: https://t.me/Baltset39_bot")
        print("💬 Напишите /start боту")
        
        # Показываем логи
        print("\n📋 Последние логи:")
        logs, _ = run_command(ssh, "journalctl -u baltset-bot -n 10 --no-pager")
        if logs:
            print(logs)
    else:
        print("\n❌ ОШИБКА ЗАПУСКА")
        print("📋 Логи:")
        logs, _ = run_command(ssh, "journalctl -u baltset-bot -n 30 --no-pager")
        if logs:
            print(logs)
    
    ssh.close()
    print("\n🎉 Деплой завершён!\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1)
