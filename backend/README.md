# Family Photo Gallery Backend

## 技术栈
- FastAPI
- MySQL（SQLAlchemy + PyMySQL）
- Pillow(EXIF 读取)

## 快速启动
1. 创建并激活虚拟环境
2. 安装依赖：
   - `pip install -r backend/requirements.txt`
3. 准备 MySQL 并设置环境变量：
   - `export GALLERY_DATABASE_URL='mysql+pymysql://wutong:wutong@127.0.0.1:3306/wutong'`
4. 运行：
   - `uvicorn app.main:app --reload --app-dir backend`

## 从 JSON 迁移到 MySQL（一次性）

如果历史版本使用过 `backend/data/*.json`，可执行：

- `python backend/scripts/migrate_json_to_mysql.py --json-dir backend/data`

迁移脚本支持重复执行（按主键/唯一键更新，不会重复新增同一条记录）。

## 默认账号
- 用户名：`admin`
- 密码：`admin123`

## 目录说明
- `backend/photos_root/`：本地开发默认照片目录
- 通过环境变量配置：
  - `GALLERY_DATABASE_URL=mysql+pymysql://wutong:wutong@127.0.0.1:3306/wutong`
  - `GALLERY_PHOTOS_ROOT=/var/lib/family-photo-gallery/photos`

## 已实现能力
- 简化 token 登录鉴权
- admin / user 角色控制
- 目录树和照片列表接口
- 点赞、评论、用户删除本人评论
- admin 手动扫描、用户创建、照片元数据编辑
- 自动周期扫描 + mtime 回退拍摄时间
