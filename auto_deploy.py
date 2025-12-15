#!/usr/bin/env python3
"""
Автоматический деплой Telegram Folders на VPS
"""

import subprocess
import sys
import time

VPS_HOST = "root@176.98.178.109"
VPS_PATH = "/root/ai_service_bots/"
PASSWORD = "vfhufhbnrf"

def run_sshpass_command(command):
    """Запуск команды через sshpass"""
    full_command = f"sshpass -p '{PASSWORD}' {command}"
    try:
        result = subprocess.run(
            full_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print("🚀 АВТОМАТИЧЕСКИЙ ДЕПЛОЙ TELEGRAM FOLDERS")
    print("=" * 50)
    print()
    
    # Проверяем наличие sshpass
    check_sshpass = subprocess.run("which sshpass", shell=True, capture_output=True)
    if check_sshpass.returncode != 0:
        print("❌ sshpass не установлен")
        print("📦 Установка sshpass...")
        install = subprocess.run("brew install hudochenkov/sshpass/sshpass", shell=True)
        if install.returncode != 0:
            print("❌ Не удалось установить sshpass")
            print("💡 Попробуйте вручную: brew install hudochenkov/sshpass/sshpass")
            return False
        print("✅ sshpass установлен")
    
    print("📤 Копирую файлы на VPS...")
    
    # Копируем файлы
    files = [
        "telegram_folders_integration.py",
        "telegram_client_bot.py"
    ]
    
    for file in files:
        print(f"  📄 {file}...")
        success, stdout, stderr = run_sshpass_command(
            f"scp {file} {VPS_HOST}:{VPS_PATH}"
        )
        if success:
            print(f"  ✅ {file} скопирован")
        else:
            print(f"  ❌ Ошибка: {stderr}")
            return False
    
    print()
    print("🔄 Перезапускаю бота...")
    
    # Останавливаем старый процесс
    print("  ⏹️  Останавливаю старый процесс...")
    run_sshpass_command(
        f"ssh {VPS_HOST} 'pkill -f telegram_client_bot.py'"
    )
    time.sleep(2)
    
    # Запускаем новый процесс
    print("  ▶️  Запускаю новый процесс...")
    success, stdout, stderr = run_sshpass_command(
        f"ssh {VPS_HOST} 'cd {VPS_PATH} && nohup python3 telegram_client_bot.py > client_bot.log 2>&1 &'"
    )
    
    time.sleep(3)
    
    # Проверяем статус
    print()
    print("🔍 Проверяю статус...")
    success, stdout, stderr = run_sshpass_command(
        f"ssh {VPS_HOST} 'ps aux | grep telegram_client_bot.py | grep -v grep'"
    )
    
    if success and stdout:
        print("✅ Бот запущен!")
        print(f"📊 Процесс: {stdout.strip()}")
    else:
        print("⚠️  Не удалось проверить статус")
    
    # Показываем логи
    print()
    print("📋 Последние логи:")
    success, stdout, stderr = run_sshpass_command(
        f"ssh {VPS_HOST} 'tail -10 {VPS_PATH}client_bot.log'"
    )
    if stdout:
        for line in stdout.strip().split('\n'):
            print(f"  {line}")
    
    print()
    print("=" * 50)
    print("✅ ДЕПЛОЙ ЗАВЕРШЕН!")
    print()
    print("🧪 Как протестировать:")
    print("  1. Откройте @ai_service_client_bot в Telegram")
    print("  2. Создайте новую заявку")
    print("  3. После подтверждения заявки появится кнопка:")
    print("     📁 Добавить папку \"⚡ Электрик БАЛТСЕТЬ\"")
    print("  4. Нажмите на кнопку - откроется Telegram с предложением")
    print("     создать папку со всеми чатами BALT-SET")
    print()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1)
