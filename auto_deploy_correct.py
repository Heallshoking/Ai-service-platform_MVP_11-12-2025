#!/usr/bin/env python3
"""
Автоматический деплой с правильным паролем VPS
"""

import subprocess
import sys
import time

VPS_HOST = "root@176.98.178.109"
VPS_PASSWORD = "pneDRE2K?Tz1k-"  # Правильный пароль из конфигурации
VPS_PATH = "/tmp/"
WEB_PATH = "/var/www/app.balt-set.ru/"
ARCHIVE = "electric-service-automation-main.tar.gz"

def run_command(cmd, shell=True):
    """Запуск команды"""
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)

def main():
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  🚀 АВТОМАТИЧЕСКИЙ ДЕПЛОЙ BALT-SET.RU")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    
    # Проверяем архив
    print("📦 Проверяю архив...")
    success, stdout, stderr = run_command(f"ls -lh {ARCHIVE}")
    if not success:
        print(f"❌ Архив не найден: {ARCHIVE}")
        print("💡 Создаю архив...")
        success, _, _ = run_command("tar -czf electric-service-automation-main.tar.gz electric-service-automation-main/")
        if not success:
            print("❌ Не удалось создать архив")
            return False
    
    print(f"✅ Архив найден: {stdout.split()[4] if stdout else 'ready'}")
    print()
    
    # Проверяем sshpass
    print("🔧 Проверяю sshpass...")
    success, _, _ = run_command("which sshpass")
    
    if not success:
        print("📥 Устанавливаю sshpass...")
        print("💡 Попытка через homebrew...")
        
        # Пробуем разные способы установки
        install_commands = [
            "brew install hudochenkov/sshpass/sshpass",
            "brew install esolitos/ipa/sshpass"
        ]
        
        installed = False
        for cmd in install_commands:
            print(f"   Пробую: {cmd}")
            success, stdout, stderr = run_command(cmd)
            if success:
                installed = True
                print("   ✅ Успешно!")
                break
            else:
                print(f"   ⚠️ Не сработало: {stderr[:100]}")
        
        if not installed:
            print()
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("  ⚠️ SSHPASS НЕ УСТАНОВЛЕН")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print()
            print("Выполните деплой вручную:")
            print()
            print("1️⃣ Скопируйте архив на VPS:")
            print(f"   scp {ARCHIVE} {VPS_HOST}:{VPS_PATH}")
            print(f"   Пароль: {VPS_PASSWORD}")
            print()
            print("2️⃣ Подключитесь к VPS:")
            print(f"   ssh {VPS_HOST}")
            print(f"   Пароль: {VPS_PASSWORD}")
            print()
            print("3️⃣ На VPS выполните:")
            print(f"   cd {VPS_PATH} && \\")
            print(f"   tar -xzf {ARCHIVE} && \\")
            print("   cd electric-service-automation-main && \\")
            print("   npm install && \\")
            print("   npm run build && \\")
            print(f"   cp -r dist/* {WEB_PATH} && \\")
            print(f"   chmod -R 755 {WEB_PATH} && \\")
            print("   echo '✅ ГОТОВО! https://app.balt-set.ru/'")
            print()
            return False
    else:
        print("✅ sshpass установлен")
    
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  📤 КОПИРОВАНИЕ НА VPS")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    
    # Копируем архив
    print(f"⏳ Копирую {ARCHIVE} на VPS...")
    cmd = f"sshpass -p '{VPS_PASSWORD}' scp {ARCHIVE} {VPS_HOST}:{VPS_PATH}"
    success, stdout, stderr = run_command(cmd)
    
    if not success:
        print(f"❌ Ошибка копирования: {stderr}")
        return False
    
    print("✅ Архив скопирован на VPS!")
    print()
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  🔨 СБОРКА НА VPS")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    
    # Команды на VPS
    vps_commands = f"""
cd {VPS_PATH} && \
tar -xzf {ARCHIVE} && \
cd electric-service-automation-main && \
npm install && \
npm run build && \
cp -r dist/* {WEB_PATH} && \
chmod -R 755 {WEB_PATH} && \
echo '✅ ДЕПЛОЙ ЗАВЕРШЕН! https://app.balt-set.ru/'
"""
    
    print("⏳ Выполняю команды на VPS...")
    print("   1. Распаковка архива...")
    print("   2. Установка зависимостей (npm install)...")
    print("   3. Сборка проекта (npm run build)...")
    print("   4. Копирование в /var/www/app.balt-set.ru/...")
    print("   5. Установка прав доступа...")
    print()
    
    cmd = f"sshpass -p '{VPS_PASSWORD}' ssh {VPS_HOST} '{vps_commands}'"
    success, stdout, stderr = run_command(cmd)
    
    if success:
        print()
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("  ✅ ДЕПЛОЙ ЗАВЕРШЕН!")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print()
        print("🌐 Проверьте сайт: https://app.balt-set.ru/")
        print()
        print("✅ Что изменилось:")
        print("  1. 'Наши услуги' → 'Услуги электрика'")
        print("  2. Система скидок за объем (3/5/11/21+ шт)")
        print("  3. Кнопка '← К услугам' в корзине")
        print()
        print("🧪 Протестируйте:")
        print("  • Найдите 'Услуги электрика' на главной")
        print("  • Добавьте 3 розетки - увидите скидку 5%")
        print("  • В корзине нажмите 'Редактировать' - увидите кнопку '← К услугам'")
        print()
        
        if stdout:
            print("📋 Вывод VPS:")
            for line in stdout.split('\n')[-10:]:
                if line.strip():
                    print(f"   {line}")
        
        return True
    else:
        print()
        print(f"❌ Ошибка выполнения на VPS:")
        print(f"   {stderr}")
        print()
        print("💡 Попробуйте выполнить команды вручную (см. выше)")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
