#!/usr/bin/env python3
import subprocess
import sys

print("\n🚀 Передеплой бота с исправлениями\n")

vps = "176.98.178.109"
password = "pneDRE2K?Tz1k-"

# Копируем файл
print("📦 Копируем обновлённый бот...")
cmd_copy = f"""
expect << 'ENDCOPY'
spawn scp telegram_lead_bot.py root@{vps}:/root/baltset_bot.py
expect "password:"
send "{password}\\r"
expect eof
ENDCOPY
"""
subprocess.run(cmd_copy, shell=True)
print("✅ Файл скопирован\n")

# Перезапускаем
print("🔄 Перезапускаем бота...")
cmd_restart = f"""
expect << 'ENDRESTART'
spawn ssh root@{vps}
expect "password:"
send "{password}\\r"
expect "#"
send "killall -9 python3; sleep 2\\r"
expect "#"
send "cd /root && nohup python3 baltset_bot.py > baltset_bot.log 2>&1 &\\r"
expect "#"
send "sleep 5\\r"
expect "#"
send "pgrep -f baltset_bot.py\\r"
expect "#"
send "echo '\\\\n📋 Логи:'\\r"
expect "#"
send "tail -15 baltset_bot.log\\r"
expect "#"
send "exit\\r"
expect eof
ENDRESTART
"""
result = subprocess.run(cmd_restart, shell=True, capture_output=True, text=True)
print(result.stdout)

print("\n🎉 Готово!\n")
print("📱 Проверьте: https://t.me/Baltset39_bot")
print("💬 Напишите /start\n")
