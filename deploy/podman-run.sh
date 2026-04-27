#!/usr/bin/env bash
#
# Podman 构建并运行单个 app 容器（需要你先准备 MySQL）。
#
#   chmod +x deploy/podman-run.sh
#   ./deploy/podman-run.sh                    # 前台运行，端口 8080 -> 容器 8000
#   HOST_PORT=9000 ./deploy/podman-run.sh
#
# 后台示例（假设本机 MySQL 在 127.0.0.1:3306）：
#   podman build -t wutong:latest .
#   podman run -d --name wutong -p 8080:8000 \
#     -e GALLERY_DATABASE_URL='mysql+pymysql://wutong:wutong@host.containers.internal:3306/wutong' \
#     -v wutong-photos:/data/photos wutong:latest
#
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_NAME="${IMAGE_NAME:-wutong:latest}"
CONTAINER_ENGINE="${CONTAINER_ENGINE:-podman}"
HOST_PORT="${HOST_PORT:-8080}"
PHOTOS_VOL="${PHOTOS_VOL:-wutong-photos}"
DB_URL="${DB_URL:-mysql+pymysql://wutong:wutong@host.containers.internal:3306/wutong}"

cd "$ROOT_DIR"

"$CONTAINER_ENGINE" build -t "$IMAGE_NAME" .

exec "$CONTAINER_ENGINE" run --rm \
  -p "${HOST_PORT}:8000" \
  -e "GALLERY_DATABASE_URL=${DB_URL}" \
  -v "${PHOTOS_VOL}:/data/photos" \
  "$IMAGE_NAME"
