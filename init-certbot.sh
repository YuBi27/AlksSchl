#!/bin/bash
# Запускати ОДИН РАЗ для отримання першого SSL сертифіката.
# Потрібно: домен aleksylya.pp.ua вже вказує на цей сервер (A-запис у DNS).

set -e

DOMAIN="aleksylya.pp.ua"
EMAIL="your@email.com"   # <-- замініть на ваш email для сповіщень від Let's Encrypt

COMPOSE="docker compose -f docker-compose.yml -f docker-compose.dev.yml"

echo "=== Крок 1: Стартуємо nginx (тільки HTTP, без SSL блоку) ==="
cp nginx/conf.d/app.conf nginx/conf.d/app.conf.bak
cat > nginx/conf.d/app.conf << 'EOF'
server {
    listen 80;
    server_name aleksylya.pp.ua;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 200 'ok';
        add_header Content-Type text/plain;
    }
}
EOF

$COMPOSE up -d nginx
$COMPOSE exec nginx nginx -t

echo "=== Перевіряємо HTTP ==="
curl -I http://aleksylya.pp.ua

echo "=== Крок 2: Отримуємо сертифікат ==="
$COMPOSE run --rm \
  --entrypoint certbot \
  certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email "$EMAIL" \
  --agree-tos \
  --no-eff-email \
  -d "$DOMAIN"

echo "=== Крок 3: Відновлюємо повний nginx конфіг з SSL ==="
cp nginx/conf.d/app.conf.bak nginx/conf.d/app.conf
rm nginx/conf.d/app.conf.bak

$COMPOSE restart nginx
$COMPOSE exec nginx nginx -t

echo ""
echo "=== Перевіряємо HTTPS ==="
curl -Iv https://aleksylya.pp.ua

echo ""
echo "✅ Готово! Тепер запустіть: make up"
