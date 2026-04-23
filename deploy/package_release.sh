#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$ROOT_DIR/dist"
RELEASE_NAME="family-photo-gallery-$(date +%Y%m%d-%H%M%S)"
STAGE_DIR="$DIST_DIR/$RELEASE_NAME"
ARCHIVE_PATH="$DIST_DIR/$RELEASE_NAME.tar.gz"

echo "[1/5] 清理并准备目录"
rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR"
mkdir -p "$DIST_DIR"

echo "[2/5] 构建前端"
npm --prefix "$ROOT_DIR/frontend" run build

echo "[3/5] 打包后端代码"
rsync -a \
  --exclude=".venv" \
  --exclude="__pycache__" \
  --exclude="*.pyc" \
  "$ROOT_DIR/backend/app" "$STAGE_DIR/backend/"
cp "$ROOT_DIR/backend/requirements.txt" "$STAGE_DIR/backend/requirements.txt"

echo "[4/5] 打包前端产物与数据目录"
rsync -a "$ROOT_DIR/frontend/dist" "$STAGE_DIR/frontend/"
rsync -a "$ROOT_DIR/backend/data" "$STAGE_DIR/backend/"
rsync -a "$ROOT_DIR/backend/photos_root" "$STAGE_DIR/backend/"

echo "[5/5] 生成压缩包"
tar -C "$DIST_DIR" -czf "$ARCHIVE_PATH" "$RELEASE_NAME"

echo ""
echo "打包完成：$ARCHIVE_PATH"
echo "解压后目录：$RELEASE_NAME"
