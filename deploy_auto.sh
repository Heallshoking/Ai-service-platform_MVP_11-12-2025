#!/bin/bash
# Полностью автоматический деплой BALT-SET.RU с использованием expect

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

VPS_HOST="root@176.98.178.109"
VPS_PASSWORD="pneDRE2K?Tz1k-"
ARCHIVE="electric-service-automation-main.tar.gz"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  🚀 АВТОМАТИЧЕСКИЙ ДЕПЛОЙ BALT-SET.RU${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Проверяем наличие expect
if ! command -v expect &> /dev/null; then
    echo -e "${YELLOW}📦 Устанавливаю expect...${NC}"
    # Для macOS через Xcode Command Line Tools (expect уже должен быть)
    if [ "$(uname)" == "Darwin" ]; then
        if ! command -v expect &> /dev/null; then
            echo -e "${RED}❌ expect не установлен${NC}"
            echo -e "${YELLOW}💡 Установите Xcode Command Line Tools:${NC}"
            echo "   xcode-select --install"
            exit 1
        fi
    fi
fi

# Проверяем архив
echo -e "${BLUE}📦 Проверяю архив...${NC}"
if [ ! -f "$ARCHIVE" ]; then
    echo -e "${YELLOW}📦 Создаю архив проекта...${NC}"
    tar -czf "$ARCHIVE" electric-service-automation-main/
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Не удалось создать архив${NC}"
        exit 1
    fi
fi

SIZE=$(ls -lh "$ARCHIVE" | awk '{print $5}')
echo -e "${GREEN}✅ Архив найден: $SIZE${NC}"
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  📤 КОПИРОВАНИЕ НА VPS${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Создаем expect скрипт для копирования
cat > /tmp/deploy_scp.exp << 'EOF'
#!/usr/bin/expect -f
set timeout 300
set password [lindex $argv 0]
set host [lindex $argv 1]
set archive [lindex $argv 2]

spawn scp $archive $host:/tmp/
expect {
    "password:" {
        send "$password\r"
        exp_continue
    }
    "yes/no" {
        send "yes\r"
        exp_continue
    }
    eof
}
EOF

chmod +x /tmp/deploy_scp.exp

echo -e "${YELLOW}⏳ Копирую архив на VPS...${NC}"
/tmp/deploy_scp.exp "$VPS_PASSWORD" "$VPS_HOST" "$ARCHIVE"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Ошибка копирования${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Архив скопирован!${NC}"
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  🔨 СБОРКА И УСТАНОВКА НА VPS${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Создаем expect скрипт для SSH
cat > /tmp/deploy_ssh.exp << 'EOF'
#!/usr/bin/expect -f
set timeout 600
set password [lindex $argv 0]
set host [lindex $argv 1]

spawn ssh $host "cd /tmp && tar -xzf electric-service-automation-main.tar.gz && cd electric-service-automation-main && npm install && npm run build && cp -r dist/* /var/www/app.balt-set.ru/ && chmod -R 755 /var/www/app.balt-set.ru/ && echo '✅ ДЕПЛОЙ ЗАВЕРШЕН!'"

expect {
    "password:" {
        send "$password\r"
        exp_continue
    }
    "yes/no" {
        send "yes\r"
        exp_continue
    }
    eof
}
EOF

chmod +x /tmp/deploy_ssh.exp

echo -e "${YELLOW}⏳ Выполняю команды на VPS:${NC}"
echo "   1. Распаковка архива..."
echo "   2. Установка зависимостей (npm install)..."
echo "   3. Сборка проекта (npm run build)..."
echo "   4. Копирование в /var/www/app.balt-set.ru/..."
echo "   5. Установка прав доступа..."
echo ""

/tmp/deploy_ssh.exp "$VPS_PASSWORD" "$VPS_HOST"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  ✅ ДЕПЛОЙ ЗАВЕРШЕН!${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${GREEN}🌐 Проверьте сайт: https://app.balt-set.ru/${NC}"
    echo ""
    echo -e "${GREEN}✅ Что изменилось:${NC}"
    echo "  1. 'Наши услуги' → 'Услуги электрика'"
    echo "  2. Система скидок за объем (3/5/11/21+ шт)"
    echo "  3. Кнопка '← К услугам' в корзине"
    echo ""
    echo -e "${YELLOW}🧪 Протестируйте:${NC}"
    echo "  • Найдите 'Услуги электрика' на главной"
    echo "  • Добавьте 3 розетки - увидите скидку 5%"
    echo "  • В корзине нажмите 'Редактировать' - увидите '← К услугам'"
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Очистка временных файлов
    rm -f /tmp/deploy_scp.exp /tmp/deploy_ssh.exp
    
    exit 0
else
    echo ""
    echo -e "${RED}❌ Ошибка выполнения на VPS${NC}"
    echo ""
    echo -e "${YELLOW}💡 Попробуйте выполнить вручную:${NC}"
    echo "   scp $ARCHIVE $VPS_HOST:/tmp/"
    echo "   ssh $VPS_HOST"
    echo "   cd /tmp && tar -xzf electric-service-automation-main.tar.gz && cd electric-service-automation-main && npm install && npm run build && cp -r dist/* /var/www/app.balt-set.ru/ && chmod -R 755 /var/www/app.balt-set.ru/"
    echo ""
    echo -e "   Пароль: ${GREEN}pneDRE2K?Tz1k-${NC}"
    echo ""
    
    # Очистка временных файлов
    rm -f /tmp/deploy_scp.exp /tmp/deploy_ssh.exp
    
    exit 1
fi
