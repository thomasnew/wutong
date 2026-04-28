#!/usr/bin/env bash

set -euo pipefail

# 备份脚本：MySQL + 照片目录
# 用法：
#   chmod +x deploy/backup_wutong.sh
#   bash deploy/backup_wutong.sh
#
# 可选环境变量：
#   BACKUP_DIR=/var/backups/wutong
#   DB_HOST=127.0.0.1
#   DB_PORT=3306
#   DB_USER=wutong
#   DB_NAME=wutong
#   DB_PASSWORD=wutong
#   PHOTOS_ROOT=/var/lib/family-photo-gallery/photos
#   RETENTION_DAYS=14

BACKUP_DIR="${BACKUP_DIR:-/var/backups/wutong}"
DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-3306}"
DB_USER="${DB_USER:-wutong}"
DB_NAME="${DB_NAME:-wutong}"
DB_PASSWORD="${DB_PASSWORD:-wutong}"
PHOTOS_ROOT="${PHOTOS_ROOT:-/var/lib/family-photo-gallery/photos}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"

TS="$(date +%F-%H%M%S)"
TARGET_DIR="${BACKUP_DIR}/${TS}"

mkdir -p "$TARGET_DIR"

echo "[1/4] 备份 MySQL: ${DB_NAME}"
MYSQL_PWD="$DB_PASSWORD" mysqldump \
  -h "$DB_HOST" \
  -P "$DB_PORT" \
  -u "$DB_USER" \
  --single-transaction \
  --quick \
  --routines \
  --triggers \
  --events \
  "$DB_NAME" | gzip > "${TARGET_DIR}/mysql-${DB_NAME}.sql.gz"

echo "[2/4] 备份照片目录: ${PHOTOS_ROOT}"
if [[ -d "$PHOTOS_ROOT" ]]; then
  tar -czf "${TARGET_DIR}/photos.tar.gz" -C "$(dirname "$PHOTOS_ROOT")" "$(basename "$PHOTOS_ROOT")"
else
  echo "警告: 照片目录不存在，跳过照片备份 -> ${PHOTOS_ROOT}"
fi

echo "[3/4] 写入校验信息"
(
  cd "$TARGET_DIR"
  sha256sum ./* > SHA256SUMS
)

echo "[4/4] 清理超过 ${RETENTION_DAYS} 天的旧备份"
find "$BACKUP_DIR" -mindepth 1 -maxdepth 1 -type d -mtime "+${RETENTION_DAYS}" -exec rm -rf {} +

echo "备份完成: ${TARGET_DIR}"
ls -lh "$TARGET_DIR"
