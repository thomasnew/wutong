# Family Photo Gallery Backend

## 技术栈
- FastAPI
- JSON 文件存储
- Pillow(EXIF 读取)

## 快速启动
1. 创建并激活虚拟环境
2. 安装依赖：
   - `pip install -r backend/requirements.txt`
3. 运行：
   - `uvicorn app.main:app --reload --app-dir backend`

## 默认账号
- 用户名：`admin`
- 密码：`admin123`

## 目录说明
- `backend/photos_root/`：本地开发默认照片目录
- `backend/data/`：本地开发默认系统 JSON 数据目录（用户、照片、评论、点赞、token）
- 生产环境建议通过环境变量外置目录：
  - `GALLERY_DATA_DIR=/var/lib/family-photo-gallery/data`
  - `GALLERY_PHOTOS_ROOT=/var/lib/family-photo-gallery/photos`

## 已实现能力
- 简化 token 登录鉴权
- admin / user 角色控制
- 目录树和照片列表接口
- 点赞、评论、用户删除本人评论
- admin 手动扫描、用户创建、照片元数据编辑
- 自动周期扫描 + mtime 回退拍摄时间
