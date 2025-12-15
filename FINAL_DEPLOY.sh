#!/usr/bin/expect -f
# ФИНАЛЬНЫЙ ДЕПЛОЙ - ТОЛЬКО БОТЫ НА VPS
set timeout 120

set vps "176.98.178.109"
set pass "pneDRE2K?Tz1k-"

puts "\n🚀 ФИНАЛЬНЫЙ ДЕПЛОЙ НА VPS...\n"

# Копируем бота клиента
puts "📤 Копирование telegram_client_bot.py..."
spawn scp telegram_client_bot.py root@$vps:/root/ai_service_bots/
expect "password:"
send "$pass\r"
expect eof

puts "📤 Копирование telegram_master_bot.py..."
spawn scp telegram_master_bot.py root@$vps:/root/ai_service_bots/
expect "password:"
send "$pass\r"
expect eof

puts "\n🔄 Перезапуск ботов...\n"

spawn ssh root@$vps
expect "password:"
send "$pass\r"
expect "#"

send "cd /root/ai_service_bots\r"
expect "#"

send "pkill -9 -f telegram_client_bot.py; pkill -9 -f telegram_master_bot.py\r"
expect "#"

send "sleep 3\r"
expect "#"

send "nohup python3 telegram_client_bot.py > client.log 2>&1 &\r"
expect "#"

send "nohup python3 telegram_master_bot.py > master.log 2>&1 &\r"
expect "#"

send "sleep 5\r"
expect "#"

puts "\n📊 СТАТУС БОТОВ:\n"
puts "==================\n"

send "if pgrep -f telegram_client_bot.py > /dev/null; then echo '✅ Клиент работает (PID:' \$(pgrep -f telegram_client_bot.py)')'; else echo '❌ Клиент НЕ работает'; fi\r"
expect "#"

send "if pgrep -f telegram_master_bot.py > /dev/null; then echo '✅ Мастер работает (PID:' \$(pgrep -f telegram_master_bot.py)')'; else echo '❌ Мастер НЕ работает'; fi\r"
expect "#"

puts "\nЛоги клиента:\n"
send "tail -3 client.log\r"
expect "#"

puts "\nЛоги мастера:\n"
send "tail -3 master.log\r"
expect "#"

send "exit\r"
expect eof

puts "\n=================================="
puts "✅ ДЕПЛОЙ ЗАВЕРШЁН!"
puts "==================================\n"
puts "📱 Боты:\n"
puts "   🙋 @ai_service_client_bot\n"
puts "   👷 @ai_service_master_bot\n"
puts "\nПроверьте их в Telegram!\n"
