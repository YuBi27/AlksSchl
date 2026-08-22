#!/bin/bash
# Запускати ОДИН РАЗ для отримання першого SSL сертифіката.
# Потрібно: домен aleksylya.pp.ua вже вказує на цей сервер (A-запис у DNS).

set -e

DOMAIN="aleksylya.pp.ua"
EMAIL="your@email.com"   # <-- замініть на ваш email для сповіщень від Let's Encrypt

COMPOSE="docker compose -f docker-compose.yml -f docker-compose.dev.yml"

echo "=== Крок 1: Завантажуємо рекомендовані параметри TLS від certbot ==="
$COMPOSE run --rm certbot sh -c "
  if [ ! -f /etc/letsencrypt/options-ssl-nginx.conf ]; then
    curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf \
      -o /etc/letsencrypt/options-ssl-nginx.conf
  fi
  if [ ! -f /etc/letsencrypt/ssl-dhparams.pem ]; then
    openssl dhparam -out /etc/letsencrypt/ssl-dhparams.pem 2048
  fi
"

echo "=== Крок 2: Стартуємо nginx (тільки HTTP, без SSL блоку) ==="
# Тимчасово коментуємо HTTPS-блок щоб nginx стартував без сертифіката
cp nginx/conf.d/app.conf nginx/conf.d/app.conf.bak
cat > nginx/conf.d/app.conf.tmp << 'EOF'
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
mv nginx/conf.d/app.conf.tmp nginx/conf.d/app.conf

$COMPOSE up -d nginx

echo "=== Крок 3: Отримуємо сертифікат ==="
$COMPOSE run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email "$EMAIL" \
  --agree-tos \
  --no-eff-email \
  -d "$DOMAIN"

echo "=== Крок 4: Відновлюємо повний nginx конфіг ==="
cp nginx/conf.d/app.conf.bak nginx/conf.d/app.conf
rm nginx/conf.d/app.conf.bak

echo "=== Крок 5: Перезавантажуємо nginx з SSL ==="
$COMPOSE restart nginx

echo ""
echo "✅ Готово! Сертифікат отримано."
echo "   Тепер запустіть: make up"
