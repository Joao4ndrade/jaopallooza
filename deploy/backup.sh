#!/bin/sh
# Backup do banco (contas, ingressos e votos). Guarda os últimos 14 dias.
# Agende na VPS com:  crontab -e   e adicione a linha:
#   0 4 * * * /opt/jaopallooza/deploy/backup.sh >> /var/log/jaopallooza-backup.log 2>&1
set -eu

cd "$(dirname "$0")/.."
mkdir -p backups
file="backups/jaopallooza-$(date +%Y-%m-%d_%H%M).sql.gz"

docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U postgres --clean --if-exists jaopallooza | gzip > "$file"

find backups -name 'jaopallooza-*.sql.gz' -mtime +14 -delete
echo "Backup salvo em $file"
