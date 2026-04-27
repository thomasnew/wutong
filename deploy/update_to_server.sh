#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BRANCH="main"
REMOTE_NAME="origin"
REMOTE_DIR="/opt/family-photo-gallery"
SERVICE_NAME="family-photo-gallery"
RELOAD_NGINX="true"
SKIP_GIT_PULL="false"
PHOTOS_ROOT="/var/lib/family-photo-gallery/photos"
DATABASE_URL="mysql+pymysql://wutong:wutong@127.0.0.1:3306/wutong"

usage() {
  cat <<EOF
用法：
  bash deploy/update_to_server.sh \\
    [--branch main] \\
    [--remote origin] \\
    [--remote-dir /opt/family-photo-gallery] \\
    [--service-name family-photo-gallery] \\
    [--photos-root /var/lib/family-photo-gallery/photos] \\
    [--database-url mysql+pymysql://wutong:wutong@127.0.0.1:3306/wutong] \\
    [--no-nginx-reload] \\
    [--skip-git-pull]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --branch)
      BRANCH="$2"
      shift 2
      ;;
    --remote)
      REMOTE_NAME="$2"
      shift 2
      ;;
    --remote-dir)
      REMOTE_DIR="$2"
      shift 2
      ;;
    --service-name)
      SERVICE_NAME="$2"
      shift 2
      ;;
    --photos-root)
      PHOTOS_ROOT="$2"
      shift 2
      ;;
    --database-url)
      DATABASE_URL="$2"
      shift 2
      ;;
    --no-nginx-reload)
      RELOAD_NGINX="false"
      shift
      ;;
    --skip-git-pull)
      SKIP_GIT_PULL="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "未知参数: $1"
      usage
      exit 1
      ;;
  esac
done

if ! command -v sudo >/dev/null 2>&1; then
  echo "缺少 sudo，无法重启系统服务。"
  exit 1
fi

if [[ ! -d "$ROOT_DIR/.git" ]]; then
  echo "当前目录不是 git 仓库：$ROOT_DIR"
  exit 1
fi

if [[ ! -x "$REMOTE_DIR/.venv/bin/pip" ]]; then
  echo "未发现已部署虚拟环境：$REMOTE_DIR/.venv"
  echo "请先执行一次完整部署（remote_setup.sh）。"
  exit 1
fi

echo "[1/6] 获取最新代码"
if [[ "$SKIP_GIT_PULL" == "false" ]]; then
  git -C "$ROOT_DIR" fetch "$REMOTE_NAME" "$BRANCH"
  git -C "$ROOT_DIR" checkout "$BRANCH"
  git -C "$ROOT_DIR" pull --ff-only "$REMOTE_NAME" "$BRANCH"
else
  echo "已跳过 git pull（--skip-git-pull）"
fi

echo "[2/6] 更新后端依赖"
"$REMOTE_DIR/.venv/bin/pip" install -r "$ROOT_DIR/backend/requirements.txt"

echo "[3/6] 构建前端"
npm --prefix "$ROOT_DIR/frontend" install
npm --prefix "$ROOT_DIR/frontend" run build

echo "[4/6] 同步代码与资源到部署目录"
sudo mkdir -p "$REMOTE_DIR"
sudo mkdir -p "$PHOTOS_ROOT"
sudo rsync -a --delete \
  --exclude=".venv" \
  --exclude="__pycache__" \
  --exclude="*.pyc" \
  "$ROOT_DIR/backend/app/" "$REMOTE_DIR/backend/app/"
sudo cp "$ROOT_DIR/backend/requirements.txt" "$REMOTE_DIR/backend/requirements.txt"
sudo rsync -a "$ROOT_DIR/frontend/dist/" "$REMOTE_DIR/frontend/dist/"
sudo chown -R "$USER":"$USER" "$REMOTE_DIR"
sudo chown -R "$USER":"$USER" "$PHOTOS_ROOT"

OVERRIDE_DIR="/etc/systemd/system/${SERVICE_NAME}.service.d"
OVERRIDE_FILE="${OVERRIDE_DIR}/override.conf"
sudo mkdir -p "$OVERRIDE_DIR"
printf "[Service]\nEnvironment=GALLERY_DATABASE_URL=%s\nEnvironment=GALLERY_PHOTOS_ROOT=%s\n" "$DATABASE_URL" "$PHOTOS_ROOT" | sudo tee "$OVERRIDE_FILE" >/dev/null

echo "[5/6] 重启后端服务"
sudo systemctl daemon-reload
sudo systemctl restart "${SERVICE_NAME}.service"
sudo systemctl is-active --quiet "${SERVICE_NAME}.service"

echo "[6/6] 可选重载 nginx"
if [[ "$RELOAD_NGINX" == "true" ]]; then
  sudo nginx -t
  sudo systemctl reload nginx
  echo "nginx 已重载。"
else
  echo "已跳过 nginx 重载（--no-nginx-reload）。"
fi

echo "增量更新完成。"
echo "- 分支: ${BRANCH}"
echo "- 服务: ${SERVICE_NAME}.service"
