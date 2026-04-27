# 梧桐家庭相册（wutong）

一个基于 `Vue3 + Vite + FastAPI` 的家庭相册系统，支持目录浏览、照片展示、点赞评论、管理员后台管理与自动扫描。

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
- 存储：JSON 文件存储（位于 `backend/data`）
- 图片元数据：`Pillow`

## 项目结构

- `frontend/`：前端工程
- `backend/`：后端工程
- `backend/photos_root/`：本地开发默认照片根目录（生产环境建议外置）
- `backend/data/`：本地开发默认 JSON 数据目录（生产环境建议外置）
- `deploy/`：打包与自动部署脚本

## 本地开发

### 1) 启动后端

```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --reload --app-dir backend
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

适用于 Debian/Ubuntu，通过 SSH 安装 **nginx**、**systemd** 后端服务；**nginx 托管前端静态文件**，后端只处理 `/api` 与 `/photos`。运行数据默认在仓库外目录，代码更新不会覆盖照片与 JSON 数据。

**首次部署**

1. 在项目根目录打包：`bash deploy/package_release.sh`
2. 一键上传到服务器并安装：`bash deploy/deploy_to_server.sh --host <服务器地址> --user <SSH 用户名> [--ssh-key ~/.ssh/id_rsa] [--remote-dir /opt/family-photo-gallery] [--domain your.domain.com] [--listen-port 8090]`  
   可选参数与服务名说明见 `deploy/README.md`。

**日后更新**

在服务器上已进入本仓库的路径后执行：`bash deploy/update_to_server.sh`  
（可选：`--branch`、`--remote-dir`、`--skip-git-pull` 等，见 `deploy/README.md`。）

默认外置目录：`/var/lib/family-photo-gallery/data`、`/var/lib/family-photo-gallery/photos`。支持跨架构部署（例如本机 ARM 打包、远端 x86 安装）。

### 方式二：容器镜像（Podman / Docker）

单容器同时提供前端静态页与后端 API（通过环境变量 `GALLERY_STATIC_ROOT`）；数据与照片请挂载卷持久化。

**构建镜像**

```bash
podman build -t wutong:latest .
```

（使用 Docker 时将 `podman` 换成 `docker`。）

**运行示例**

```bash
podman run --rm -p 8080:8000 \
  -v wutong-data:/data/app \
  -v wutong-photos:/data/photos \
  wutong:latest
```

或使用脚本：`chmod +x deploy/podman-run.sh && ./deploy/podman-run.sh`  
浏览器访问：`http://localhost:8080`（映射到容器内 `8000`）。可用环境变量 `HOST_PORT`、`CONTAINER_ENGINE=docker` 调整端口或改用 Docker。

## 后端关键配置

后端配置位于 `backend/app/core/config.py`，支持通过环境变量覆盖（前缀 `GALLERY_`），例如：

- `GALLERY_DATA_DIR`
- `GALLERY_PHOTOS_ROOT`
- `GALLERY_TOKEN_TTL_DAYS`
- `GALLERY_SCAN_INTERVAL_SECONDS`
- `GALLERY_ADMIN_DEFAULT_USERNAME`
- `GALLERY_ADMIN_DEFAULT_PASSWORD`
- `GALLERY_STATIC_ROOT`（容器镜像内已设置；服务器直接部署一般不设，由 nginx 提供前端）

本地开发默认使用 `backend/data` 与 `backend/photos_root`。服务器直接部署时，`deploy` 脚本会在 systemd 中注入 `GALLERY_DATA_DIR`、`GALLERY_PHOTOS_ROOT`。

## 后续建议

- 增加自动化测试（后端 API 与前端 E2E）
- 上线时启用 HTTPS（例如 `nginx + certbot`）