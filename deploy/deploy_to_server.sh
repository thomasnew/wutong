#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE_HOST=""
REMOTE_USER=""
REMOTE_PORT="22"
SSH_KEY=""
REMOTE_DIR="/opt/family-photo-gallery"
SERVICE_NAME="family-photo-gallery"
SITE_NAME="family-photo-gallery"
DOMAIN="_"
SKIP_PACKAGE="false"
ARCHIVE_PATH=""

LOCAL_ARCH="$(uname -m)"

usage() {
  cat <<EOF
用法：
  bash deploy/deploy_to_server.sh \\
    --host <服务器IP或域名> \\
    --user <SSH用户名> \\
    [--port 22] \\
    [--ssh-key ~/.ssh/id_rsa] \\
    [--remote-dir /opt/family-photo-gallery] \\
    [--service-name family-photo-gallery] \\
    [--site-name family-photo-gallery] \\
    [--domain your.domain.com] \\
    [--skip-package]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host)
      REMOTE_HOST="$2"
      shift 2
      ;;
    --user)
      REMOTE_USER="$2"
      shift 2
      ;;
    --port)
      REMOTE_PORT="$2"
      shift 2
      ;;
    --ssh-key)
      SSH_KEY="$2"
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
    --site-name)
      SITE_NAME="$2"
      shift 2
      ;;
    --domain)
      DOMAIN="$2"
      shift 2
      ;;
    --skip-package)
      SKIP_PACKAGE="true"
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

if [[ -z "$REMOTE_HOST" || -z "$REMOTE_USER" ]]; then
  echo "必须提供 --host 和 --user 参数"
  usage
  exit 1
fi

echo "本地架构: ${LOCAL_ARCH}"

if [[ "$SKIP_PACKAGE" == "false" ]]; then
  bash "$ROOT_DIR/deploy/package_release.sh"
fi

shopt -s nullglob
archives=("$ROOT_DIR"/dist/family-photo-gallery-*.tar.gz)
shopt -u nullglob
if [[ ${#archives[@]} -eq 0 ]]; then
  echo "未找到发布包，请先执行打包。"
  exit 1
fi
IFS=$'\n' sorted_archives=($(printf '%s\n' "${archives[@]}" | sort -r))
unset IFS
ARCHIVE_PATH="${sorted_archives[0]}"

SSH_OPTS=(-p "$REMOTE_PORT")
if [[ -n "$SSH_KEY" ]]; then
  SSH_OPTS+=(-i "$SSH_KEY")
fi

REMOTE_ARCHIVE="/tmp/$(basename "$ARCHIVE_PATH")"
REMOTE_SCRIPT="/tmp/remote_setup.sh"

echo "[1/4] 上传发布包"
scp "${SSH_OPTS[@]}" "$ARCHIVE_PATH" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_ARCHIVE}"

echo "[2/4] 上传远程部署脚本"
scp "${SSH_OPTS[@]}" "$ROOT_DIR/deploy/remote_setup.sh" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_SCRIPT}"

REMOTE_ARCH="$(ssh "${SSH_OPTS[@]}" "${REMOTE_USER}@${REMOTE_HOST}" "uname -m")"
echo "远端架构: ${REMOTE_ARCH}"
if [[ "$REMOTE_ARCH" != "$LOCAL_ARCH" ]]; then
  echo "提示: 检测到跨架构部署（${LOCAL_ARCH} -> ${REMOTE_ARCH}），本方案仅上传源码/静态资源并在远端重装依赖，可安全部署。"
fi

echo "[3/4] 执行远程部署"
ssh "${SSH_OPTS[@]}" "${REMOTE_USER}@${REMOTE_HOST}" \
  "chmod +x ${REMOTE_SCRIPT} && bash ${REMOTE_SCRIPT} \
    --archive ${REMOTE_ARCHIVE} \
    --remote-dir ${REMOTE_DIR} \
    --service-name ${SERVICE_NAME} \
    --site-name ${SITE_NAME} \
    --domain ${DOMAIN}"

echo "[4/4] 清理远程脚本"
ssh "${SSH_OPTS[@]}" "${REMOTE_USER}@${REMOTE_HOST}" "rm -f ${REMOTE_SCRIPT}"

echo "全部完成：${REMOTE_USER}@${REMOTE_HOST}"
