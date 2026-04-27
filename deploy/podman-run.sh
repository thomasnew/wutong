#!/usr/bin/env bash
#
# Podman 构建并运行（Docker 可把 CONTAINER_ENGINE=docker）。
#
#   chmod +x deploy/podman-run.sh
#   ./deploy/podman-run.sh                    # 前台运行，端口 8080 -> 容器 8000
#   HOST_PORT=9000 ./deploy/podman-run.sh
#
# 后台示例：
#   podman build -t wutong:latest .
#   podman run -d --name wutong -p 8080:8000 \
#     -v wutong-data:/data/app -v wutong-photos:/data/photos wutong:latest
#
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_NAME="${IMAGE_NAME:-wutong:latest}"
CONTAINER_ENGINE="${CONTAINER_ENGINE:-podman}"
HOST_PORT="${HOST_PORT:-8080}"
DATA_VOL="${DATA_VOL:-wutong-data}"
PHOTOS_VOL="${PHOTOS_VOL:-wutong-photos}"

cd "$ROOT_DIR"

"$CONTAINER_ENGINE" build -t "$IMAGE_NAME" .

exec "$CONTAINER_ENGINE" run --rm \
  -p "${HOST_PORT}:8000" \
  -v "${DATA_VOL}:/data/app" \
  -v "${PHOTOS_VOL}:/data/photos" \
  "$IMAGE_NAME"
