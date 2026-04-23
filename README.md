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
- `backend/photos_root/`：照片根目录（支持软链接到其他目录）
- `backend/data/`：用户/照片/评论/点赞/token 等 JSON 数据
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

## 打包与部署

已提供完整自动化脚本，见 `deploy/README.md`。常用命令：

```bash
# 本地打包
bash deploy/package_release.sh

# 一键部署到远端服务器
bash deploy/deploy_to_server.sh \
  --host <server-ip-or-domain> \
  --user <ssh-user> \
  --ssh-key ~/.ssh/id_rsa \
  --remote-dir /opt/family-photo-gallery \
  --domain <your-domain>
```

说明：

- 支持跨架构部署（例如本地 `arm64` Mac mini 部署到 `x86_64` Linux）
- 发布包不携带本机虚拟环境，远端按自身架构重建 Python 依赖

## 后端关键配置

后端配置位于 `backend/app/core/config.py`，支持通过环境变量覆盖（前缀 `GALLERY_`），例如：

- `GALLERY_DATA_DIR`
- `GALLERY_PHOTOS_ROOT`
- `GALLERY_TOKEN_TTL_DAYS`
- `GALLERY_SCAN_INTERVAL_SECONDS`
- `GALLERY_ADMIN_DEFAULT_USERNAME`
- `GALLERY_ADMIN_DEFAULT_PASSWORD`

## 后续建议

- 增加 `.gitignore`（忽略 `dist/*.tar.gz`、`.venv`、`node_modules` 等）
- 增加自动化测试（后端 API 测试与前端 E2E）
- 上线时启用 HTTPS（`nginx + certbot`）