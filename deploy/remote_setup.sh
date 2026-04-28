#!/usr/bin/env bash

set -euo pipefail

ARCHIVE_PATH=""
REMOTE_DIR="/opt/family-photo-gallery"
SERVICE_NAME="family-photo-gallery"
SITE_NAME="family-photo-gallery"
DOMAIN="_"
LISTEN_PORT="443"
PHOTOS_ROOT="/var/lib/family-photo-gallery/photos"
DATABASE_URL="mysql+pymysql://wutong:wutong@127.0.0.1:3306/wutong"
ENABLE_HTTPS="true"
SSL_CERT_PATH=""
SSL_KEY_PATH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --archive)
      ARCHIVE_PATH="$2"
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
    --listen-port)
      LISTEN_PORT="$2"
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
    --enable-https)
      ENABLE_HTTPS="$2"
      shift 2
      ;;
    --ssl-cert-path)
      SSL_CERT_PATH="$2"
      shift 2
      ;;
    --ssl-key-path)
      SSL_KEY_PATH="$2"
      shift 2
      ;;
    *)
      echo "未知参数: $1"
      exit 1
      ;;
  esac
done

if [[ -z "$ARCHIVE_PATH" ]]; then
  echo "必须传入 --archive <远程压缩包路径>"
  exit 1
fi

if [[ ! -f "$ARCHIVE_PATH" ]]; then
  echo "找不到压缩包: $ARCHIVE_PATH"
  exit 1
fi

if ! [[ "$LISTEN_PORT" =~ ^[0-9]+$ ]] || [[ "$LISTEN_PORT" -lt 1 ]] || [[ "$LISTEN_PORT" -gt 65535 ]]; then
  echo "端口无效: $LISTEN_PORT (应为 1-65535)"
  exit 1
fi

if [[ "$ENABLE_HTTPS" != "true" && "$ENABLE_HTTPS" != "false" ]]; then
  echo "参数 --enable-https 仅支持 true/false"
  exit 1
fi

if [[ "$ENABLE_HTTPS" == "true" ]]; then
  if [[ -z "$SSL_CERT_PATH" && "$DOMAIN" != "_" ]]; then
    SSL_CERT_PATH="/etc/letsencrypt/live/${DOMAIN}/fullchain.pem"
  fi
  if [[ -z "$SSL_KEY_PATH" && "$DOMAIN" != "_" ]]; then
    SSL_KEY_PATH="/etc/letsencrypt/live/${DOMAIN}/privkey.pem"
  fi
  if [[ -z "$SSL_CERT_PATH" || -z "$SSL_KEY_PATH" ]]; then
    echo "HTTPS 已启用，但证书路径为空。请传入 --ssl-cert-path 与 --ssl-key-path。"
    exit 1
  fi
  if [[ ! -f "$SSL_CERT_PATH" || ! -f "$SSL_KEY_PATH" ]]; then
    echo "HTTPS 证书文件不存在："
    echo "  cert: $SSL_CERT_PATH"
    echo "  key : $SSL_KEY_PATH"
    exit 1
  fi
fi

if ! command -v sudo >/dev/null 2>&1; then
  echo "目标机器缺少 sudo，无法自动安装系统服务和 nginx。"
  exit 1
fi

REMOTE_ARCH="$(uname -m)"
echo "目标机器架构: ${REMOTE_ARCH}"

echo "[1/8] 安装系统依赖 (python3-venv + nginx + 构建依赖)"
sudo apt-get update
sudo apt-get install -y \
  python3 \
  python3-venv \
  python3-dev \
  build-essential \
  libjpeg-dev \
  zlib1g-dev \
  nginx

echo "[2/8] 解压发布包到 $REMOTE_DIR"
sudo mkdir -p "$REMOTE_DIR"
sudo tar -xzf "$ARCHIVE_PATH" -C "$REMOTE_DIR" --strip-components=1
sudo chown -R "$USER":"$USER" "$REMOTE_DIR"

echo "[3/8] 创建虚拟环境并安装后端依赖"
python3 -m venv "$REMOTE_DIR/.venv"
"$REMOTE_DIR/.venv/bin/pip" install --upgrade pip
"$REMOTE_DIR/.venv/bin/pip" install -r "$REMOTE_DIR/backend/requirements.txt"

echo "[4/8] 初始化运行媒体目录（仓库外）"
sudo mkdir -p "$PHOTOS_ROOT"
sudo chown -R "$USER":"$USER" "$PHOTOS_ROOT"

echo "[5/8] 写入 systemd 服务"
SERVICE_FILE="/tmp/${SERVICE_NAME}.service"
cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Family Photo Gallery API
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$REMOTE_DIR
Environment=GALLERY_DATABASE_URL=$DATABASE_URL
Environment=GALLERY_PHOTOS_ROOT=$PHOTOS_ROOT
ExecStart=$REMOTE_DIR/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir $REMOTE_DIR/backend
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
sudo mv "$SERVICE_FILE" "/etc/systemd/system/${SERVICE_NAME}.service"

echo "[6/8] 写入 nginx 站点配置"
NGINX_FILE="/tmp/${SITE_NAME}.conf"
if [[ "$ENABLE_HTTPS" == "true" ]]; then
cat > "$NGINX_FILE" <<EOF
server {
    listen 80;
    server_name ${DOMAIN};
    return 301 https://\$host\$request_uri;
}

server {
    listen ${LISTEN_PORT} ssl http2;
    server_name ${DOMAIN};
    ssl_certificate ${SSL_CERT_PATH};
    ssl_certificate_key ${SSL_KEY_PATH};

    root ${REMOTE_DIR}/frontend/dist;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /photos/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
else
cat > "$NGINX_FILE" <<EOF
server {
    listen ${LISTEN_PORT};
    server_name ${DOMAIN};

    root ${REMOTE_DIR}/frontend/dist;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /photos/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
fi
sudo mv "$NGINX_FILE" "/etc/nginx/sites-available/${SITE_NAME}.conf"
sudo ln -sf "/etc/nginx/sites-available/${SITE_NAME}.conf" "/etc/nginx/sites-enabled/${SITE_NAME}.conf"

echo "[7/8] 启动/重启服务"
sudo systemctl daemon-reload
sudo systemctl enable --now "${SERVICE_NAME}.service"
sudo nginx -t
sudo systemctl restart nginx

echo "[8/8] 清理临时包"
rm -f "$ARCHIVE_PATH"

SERVER_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
if [[ -z "${SERVER_IP}" ]]; then
  SERVER_IP="$(hostname 2>/dev/null || true)"
fi

echo "部署完成。"
echo "- API: 由 systemd 服务 ${SERVICE_NAME}.service 管理"
echo "- Web: 由 nginx 站点 ${SITE_NAME}.conf 提供"
echo "- 数据库连接: ${DATABASE_URL}"
echo "- 媒体目录: ${PHOTOS_ROOT}"
echo "- 监听端口: ${LISTEN_PORT}"
if [[ "$ENABLE_HTTPS" == "true" ]]; then
  echo "- 可访问地址(IP): https://${SERVER_IP}:${LISTEN_PORT}/"
else
  echo "- 可访问地址(IP): http://${SERVER_IP}:${LISTEN_PORT}/"
fi
if [[ "${DOMAIN}" != "_" ]]; then
  if [[ "$ENABLE_HTTPS" == "true" ]]; then
    echo "- 可访问地址(域名): https://${DOMAIN}:${LISTEN_PORT}/"
  else
    echo "- 可访问地址(域名): http://${DOMAIN}:${LISTEN_PORT}/"
  fi
fi
