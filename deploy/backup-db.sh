#!/usr/bin/env bash
# Sao lưu DB app web mỗi đêm (cron /etc/cron.d/pmnhap-backup, biên bản docs/soatdeploy-02-11-2026.md).
# File chứa số căn cước + số GPLX: chỉ root đọc, giữ 7 ngày rồi tự xóa. Hỏng cả VPS thì mất luôn bản này.
set -euo pipefail
umask 077

APP=/opt/nhaphocvien
DICH=/var/backups/nhaphocvien
GIU_NGAY=7

mkdir -p "$DICH"
chmod 700 "$DICH"
TEN="$DICH/nhaphocvien-$(date +%Y%m%d-%H%M%S).sql.gz"
TAM="$TEN.tam"
trap 'rm -f "$TAM"' EXIT

cd "$APP"
docker compose -f docker-compose.prod.yml exec -T postgres \
  sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' | gzip > "$TAM"

# Chỉ nhận file đọc được và có đủ phần cuối của pg_dump; hỏng thì giữ nguyên các bản cũ.
gzip -t "$TAM"
zcat "$TAM" | tail -n 5 | grep -q "PostgreSQL database dump complete"
mv "$TAM" "$TEN"

find "$DICH" -name 'nhaphocvien-*.sql.gz' -type f -mtime +"$GIU_NGAY" -delete
echo "$(date '+%F %T') OK $(basename "$TEN") $(du -h "$TEN" | cut -f1)"
