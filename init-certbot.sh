#!/bin/bash
# Запускати ОДИН РАЗ для отримання першого SSL сертифіката.
# Потрібно: домен aleksylya.pp.ua вже вказує на цей сервер (A-запис у DNS).

set -e

DOMAIN="aleksylya.pp.ua"
EMAIL="your@email.com"   # <-- замініть на ваш email для сповіщень від Let's Encrypt

COMPOSE="docker compose"

# --- Прибираємо залишки попереднього запуску ---
# Якщо попередній запуск завис і .bak існує — відновлюємо оригінальний конфіг
if [ -f nginx/conf.d/app.conf.bak ]; then
    echo "Знайдено app.conf.bak від попереднього запуску — відновлюємо..."
    cp nginx/conf.d/app.conf.bak nginx/conf.d/app.conf
    rm nginx/conf.d/app.conf.bak
fi

# Зупиняємо nginx якщо він запущений
$COMPOSE stop nginx 2>/dev/null || true

echo "=== Крок 1: Підміняємо конфіг на тимчасовий HTTP-only (без proxy_pass) ==="
cp nginx/conf.d/app.conf nginx/conf.d/app.conf.bak
cat > nginx/conf.d/app.conf << 'EOF'
server {
    listen 80;
    server_name aleksylya.pp.ua;

    # ACME challenge для Let's Encrypt
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 200 'ok';
        add_header Content-Type text/plain;
    }
}
EOF

echo "=== Крок 2: Стартуємо тільки nginx (без bot/api) ==="
$COMPOSE up -d nginx

echo "Чекаємо 3 секунди поки nginx стартує..."
sleep 3

$COMPOSE exec nginx nginx -t

echo "=== Перевіряємо HTTP ==="
curl -sf http://$DOMAIN > /dev/null && echo "HTTP OK" || echo "УВАГА: HTTP не відповідає — перевірте DNS і firewall"

echo "=== Крок 3: Отримуємо сертифікат ==="
$COMPOSE run --rm \
  --entrypoint certbot \
  certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email "$EMAIL" \
  --agree-tos \
  --no-eff-email \
  -d "$DOMAIN"

echo "=== Крок 4: Відновлюємо повний nginx конфіг з SSL ==="
cp nginx/conf.d/app.conf.bak nginx/conf.d/app.conf
rm nginx/conf.d/app.conf.bak

echo "=== Крок 5: Перезапускаємо nginx з SSL конфігом ==="
# Спочатку потрібні сервіси щоб nginx міг резолвити 'bot'
$COMPOSE up -d db redis
echo "Чекаємо поки db і redis стануть healthy..."
sleep 10

$COMPOSE up -d api
echo "Чекаємо поки api стане healthy (до 60 сек)..."
sleep 20

$COMPOSE up -d bot
sleep 5

$COMPOSE restart nginx
$COMPOSE exec nginx nginx -t

echo ""
echo "=== Перевіряємо HTTPS ==="
curl -Iv https://$DOMAIN 2>&1 | grep -E 'HTTP/|subject:|issuer:|SSL certificate verify ok'

echo ""
echo "✅ Готово! Сертифікат отримано, всі сервіси запущені."
echo "   Для перевірки: docker compose ps"
