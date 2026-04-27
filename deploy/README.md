# 部署脚本说明

本目录提供了两个核心能力：

1. **整体打包**：把前端构建产物 + 后端代码打成发布包（不包含运行数据）。
2. **自动部署**：把发布包上传到目标服务器，并自动配置 `systemd + nginx`。

## 文件说明

- `deploy/package_release.sh`：本地打包脚本。
- `deploy/deploy_to_server.sh`：本地一键部署入口（会自动上传并触发远程安装）。
- `deploy/remote_setup.sh`：远程执行脚本（由 `deploy_to_server.sh` 上传并执行）。
- `deploy/update_to_server.sh`：服务器本机增量更新脚本（拉新代码并自动重启服务）。

## 1) 本地打包

在项目根目录执行：

```bash
bash deploy/package_release.sh
```

打包完成后会在 `dist/` 生成：

- `family-photo-gallery-YYYYMMDD-HHMMSS/`（解压目录）
- `family-photo-gallery-YYYYMMDD-HHMMSS.tar.gz`（发布包）

## 2) 一键部署到服务器

> 目标服务器要求：Debian/Ubuntu 系，具备 `sudo` 权限与 `apt-get`。
>
> 支持跨架构部署（例如本地 `arm64` 的 Mac mini 部署到 `x86_64` 服务器）：发布包只包含源码与前端静态资源，不携带本机 Python 虚拟环境或 Node 原生二进制，远端会按自身架构重新安装依赖。

```bash
bash deploy/deploy_to_server.sh \
  --host 1.2.3.4 \
  --user ubuntu \
  --ssh-key ~/.ssh/id_rsa \
  --remote-dir /opt/family-photo-gallery \
  --domain your.domain.com \
  --listen-port 8090
```

常用可选参数：

- `--port 22`：SSH 端口
- `--service-name family-photo-gallery`：systemd 服务名
- `--site-name family-photo-gallery`：nginx 站点名
- `--listen-port 8090`：nginx 监听端口（默认 8090）
- `--data-dir /var/lib/family-photo-gallery/data`：运行数据目录（仓库外）
- `--photos-root /var/lib/family-photo-gallery/photos`：照片目录（仓库外）
- `--skip-package`：跳过重新打包，直接部署最近一次包

重要说明：

- 生产环境的数据与媒体目录默认在仓库外（`/var/lib/family-photo-gallery`）。
- `git pull` / 代码更新不会删除这些目录中的照片、点赞、评论数据。

## 部署后的服务位置

- 后端服务：`/etc/systemd/system/<service-name>.service`
- nginx 配置：`/etc/nginx/sites-available/<site-name>.conf`
- 项目目录：`<remote-dir>`

## 3) 服务器本机增量更新（已 clone 场景）

在服务器项目目录执行：

```bash
bash deploy/update_to_server.sh
```

默认行为：

- `git pull --ff-only origin main`
- 更新后端依赖
- 重建前端
- 同步到部署目录（默认 `/opt/family-photo-gallery`）
- 自动重启 `family-photo-gallery.service`
- 自动校验并重载 `nginx`

常用可选参数：

- `--branch main`：更新分支
- `--remote origin`：远端名
- `--remote-dir /opt/family-photo-gallery`：部署目录
- `--service-name family-photo-gallery`：systemd 服务名
- `--data-dir /var/lib/family-photo-gallery/data`：运行数据目录（用于初始化目录）
- `--photos-root /var/lib/family-photo-gallery/photos`：照片目录（用于初始化目录）
- `--no-nginx-reload`：跳过 nginx 重载
- `--skip-git-pull`：跳过拉代码（只做本地增量发布）

## 常用运维命令（服务器上执行）

```bash
sudo systemctl status family-photo-gallery
sudo journalctl -u family-photo-gallery -n 200 --no-pager
sudo nginx -t
sudo systemctl restart nginx
```
