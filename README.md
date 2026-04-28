# 梧桐家庭相册（wutong）

一个基于 `Vue3 + Vite + FastAPI` 的家庭相册系统，支持目录浏览、照片展示、点赞评论、管理员后台管理与自动扫描。

## 效果图

### 排行榜

![排行榜](./排行榜.png)

### 照片墙

![照片墙](./照片墙.png)

## 功能概览

- 多用户登录与角色权限（`admin` / `user`）
- 照片目录树与照片列表展示
- 点赞、评论、删除本人评论
- 管理员能力：手动扫描、用户管理、照片元数据编辑、跑马灯速度设置
- 照片元数据解析（EXIF 时间/GPS，缺失时回退到文件 `mtime`）
- 自动周期扫描 + 手动触发扫描
- 支持在 `backend/photos_root` 下使用目录软链接扫描外部照片目录（含循环链接保护）

## 技术栈

- 前端：`Vue 3`、`Vue Router`、`Vite`
- 后端：`FastAPI`、`Pydantic`
- 存储：`MySQL`（`SQLAlchemy + PyMySQL`）
- 图片元数据：`Pillow`

## 项目结构

- `frontend/`：前端工程
- `backend/`：后端工程
- `backend/photos_root/`：照片根目录（默认本地目录，可通过环境变量外置）
- `podman-compose.yml`：`app + mysql` 双容器编排文件
- `deploy/`：打包与自动部署脚本

## 本地开发

### 1) 启动后端

```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt
export GALLERY_DATABASE_URL='mysql+pymysql://wutong:wutong@127.0.0.1:3306/wutong'
uvicorn app.main:app --reload --app-dir backend
```

如需把历史 `backend/data` JSON 数据迁移到 MySQL，可执行：

```bash
python backend/scripts/migrate_json_to_mysql.py --json-dir backend/data
```

默认监听 `http://127.0.0.1:8000`。

### 2) 启动前端

```bash
cd frontend
npm install
npm run dev
```

默认监听 `http://127.0.0.1:5173`，并通过 Vite 代理到后端的 `/api` 与 `/photos`。

## 默认账号

- 用户名：`admin`
- 密码：`admin123`

建议首次登录后由管理员修改密码并新增普通用户。

## 部署（两种方式任选其一）

### 方式一：服务器直接部署（nginx + systemd）

适用于 Debian/Ubuntu，通过 SSH 安装 **nginx**、**systemd** 后端服务；**nginx 托管前端静态文件**，后端只处理 `/api` 与 `/photos`。数据库使用 MySQL（可本机或远程）。

**首次部署**

1. 在项目根目录打包：`bash deploy/package_release.sh`
2. 一键上传到服务器并安装：`bash deploy/deploy_to_server.sh --host <服务器地址> --user <SSH 用户名> [--ssh-key ~/.ssh/id_rsa] [--remote-dir /opt/family-photo-gallery] [--domain your.domain.com] [--listen-port 443]`  
   可选参数与服务名说明见 `deploy/README.md`。

**日后更新**

在服务器上已进入本仓库的路径后执行：`bash deploy/update_to_server.sh`  
（可选：`--branch`、`--remote-dir`、`--skip-git-pull` 等，见 `deploy/README.md`。）

默认外置媒体目录：`/var/lib/family-photo-gallery/photos`。支持跨架构部署（例如本机 ARM 打包、远端 x86 安装）。
默认启用 HTTPS（80 自动跳转到 443），请提前准备证书，或通过 `--disable-https` 临时使用 HTTP。

### 方式二：容器部署（Podman Compose，app + db）

默认提供 `app + mysql` 两个容器，`app` 同时提供前端静态页与后端 API。

**启动**

```bash
podman-compose -f podman-compose.yml up -d --build
```

**停止**

```bash
podman-compose -f podman-compose.yml down
```

服务端口：

- Web/API：`http://127.0.0.1:8080`
- MySQL：`127.0.0.1:3306`（默认账号 `wutong/wutong`，库 `wutong`）

如需单容器直连现有 MySQL，也可使用：

```bash
chmod +x deploy/podman-run.sh
./deploy/podman-run.sh
```

## 后端关键配置

后端配置位于 `backend/app/core/config.py`，支持通过环境变量覆盖（前缀 `GALLERY_`），例如：

- `GALLERY_DATABASE_URL`
- `GALLERY_PHOTOS_ROOT`
- `GALLERY_TOKEN_TTL_DAYS`
- `GALLERY_SCAN_INTERVAL_SECONDS`
- `GALLERY_ADMIN_DEFAULT_USERNAME`
- `GALLERY_ADMIN_DEFAULT_PASSWORD`
- `GALLERY_STATIC_ROOT`（容器镜像内已设置；服务器直接部署一般不设，由 nginx 提供前端）

服务器直接部署时，`deploy` 脚本会在 systemd 中注入 `GALLERY_DATABASE_URL` 与 `GALLERY_PHOTOS_ROOT`。

## 后续建议

- 增加自动化测试（后端 API 与前端 E2E）
- 上线时启用 HTTPS（例如 `nginx + certbot`）