#!/usr/bin/expect -f
# Автоматический деплой Google Sheets Integration на VPS
# Usage: ./DEPLOY_GOOGLE_SHEETS.sh

set timeout 60
set password "vfhufhbnrf"
set server "176.98.178.109"
set user "root"
set remote_dir "/root/ai_service_bots"

puts "\n🚀 Деплой Google Sheets Integration на VPS...\n"

# 1. Копируем google_sheets_integration.py
puts "📤 Копирование google_sheets_integration.py..."
spawn scp google_sheets_integration.py ${user}@${server}:${remote_dir}/
expect {
    "password:" {
        send "${password}\r"
        expect eof
    }
    eof
}

# 2. Копируем обновленный telegram_client_bot.py
puts "📤 Копирование обновленного telegram_client_bot.py..."
spawn scp telegram_client_bot.py ${user}@${server}:${remote_dir}/
expect {
    "password:" {
        send "${password}\r"
        expect eof
    }
    eof
}

# 3. Устанавливаем зависимости и перезапускаем бота
puts "🔧 Установка зависимостей и перезапуск бота..."
spawn ssh ${user}@${server}
expect {
    "password:" {
        send "${password}\r"
        expect "# " {
            # Устанавливаем зависимости
            send "pip3 install gspread oauth2client\r"
            expect "# " {
                # Переходим в папку ботов
                send "cd ${remote_dir}\r"
                expect "# " {
                    # Останавливаем клиентского бота
                    send "pkill -f telegram_client_bot.py\r"
                    expect "# " {
                        # Ждем 2 секунды
                        send "sleep 2\r"
                        expect "# " {
                            # Запускаем клиентского бота
                            send "nohup python3 telegram_client_bot.py > client_bot.log 2>&1 &\r"
                            expect "# " {
                                # Проверяем статус
                                send "ps aux | grep telegram_client_bot.py | grep -v grep\r"
                                expect "# " {
                                    # Выходим
                                    send "exit\r"
                                    expect eof
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

puts "\n✅ Деплой завершен!"
puts "📋 Следующие шаги:"
puts "1. Создайте Google Cloud проект и Service Account"
puts "2. Скачайте credentials.json"
puts "3. Загрузите credentials.json на VPS: scp credentials.json root@176.98.178.109:/root/ai_service_bots/"
puts "4. Создайте Google Таблицу 'BALT-SET Заявки'"
puts "5. Поделитесь таблицей с Service Account email"
puts "\n📖 Подробная инструкция: НАСТРОЙКА_GOOGLE_SHEETS.md\n"
