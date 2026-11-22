# Postiz 社交媒体全平台自动发布中枢部署指南

本项目集成了顶级开源多平台发布工具 **Postiz (gitroomhq/postiz-app)**，用于自动化将 MemeMorph 宣发内容排期并批量推送至全球主流社交与开发者平台。

---

## 🚀 方式一：本地 Docker 一键部署 (推荐)

### 1. 运行环境要求
* Windows 10/11 (已安装 Docker Desktop 与 WSL2)
* 内存推荐 $\ge$ 8GB

### 2. 一键启动
进入 `deploy/postiz` 目录，双击运行：
```powershell
.\start_postiz.bat
```
或在终端执行：
```bash
docker compose up -d
```
启动后，Postiz 将运行在：
* **Web 管理控制台**：`http://localhost:5000`
* **PostgreSQL 数据持久化**：端口 `5432`
* **Redis 任务队列**：端口 `6379`

### 3. 首次配置
1. 浏览器打开 `http://localhost:5000`；
2. 输入邮箱和密码注册本地首个管理员账号；
3. 进入 **Settings -> Integrations**；
4. 点击需要宣发的平台（Twitter/X, Reddit, LinkedIn, YouTube, TikTok 等）绑定授权；
5. 进入 **New Post**，粘贴我们为您定制的宣发文案与截图，点击 **Schedule / Publish Now** 即可一键全网分发！

---

## ☁️ 方式二：免部署云端快速通道 (零本地资源占用)

如果您希望省去本地 Docker 镜像拉取与资源开销，可直接使用官方免费托管版：
1. 访问 [Postiz 官方云端版 (app.postiz.com)](https://app.postiz.com/)；
2. 免费注册账号并直接进入仪表盘；
3. 绑定社交平台账号（通过 OAuth 授权一次完成）；
4. 直接使用宣发物料库中的中英文模版排期发布。
