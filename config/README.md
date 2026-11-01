# 顶层配置目录说明 (`config/`)

## 1. 职责边界与定位 (ADR-P0-02 / ADR-P0-06)
- **Django 运行时设置归属**：所有 Django/Wagtail 运行时设置（如 `base.py`、`dev.py`、`production.py`）统一定义在 Python 核心产品根包内（`src/wagtailblog2/settings/`），以确保 Python 打包分发、可编辑安装及测试发现时的导入一致性。
- **本目录 (`config/`) 职责**：仅用于存放外部部署、基础设施编排与静态工具配置，例如：
  - Nginx 反向代理配置模板；
  - Systemd 服务与 Socket 单元模板；
  - 容器编排 (Docker / Podman / Compose) 配置文件；
  - 静态代码检查与 CI 工具专用配置文件。

## 2. 隔离与安全红线
1. 本目录下的任何部署或系统配置文件均属于**待审定资料**，不构成当前执行授权；
2. 严禁在本目录中存放含有真实生产凭据、数据库密码或私钥的文件；
3. 严禁将本目录作为 Django `DJANGO_SETTINGS_MODULE` 的直接加载包，避免与 `src/wagtailblog2/` 形成双重根路径冲突。

## 3. 基础设施配置键占位说明（仅文档，不构成连接授权）
配置键的占位示例见仓库根目录 `.env.example`（**外部服务配置键**全部为注释和 `<占位符>`；Django/SQLite/开发值仍是本地骨架的有效安全默认值）。启用顺序以 `说明书/00-产品需求与项目管理/12-新站基础设施与数据库初始化方案.md` 为准，该文档目前仍是待审定提案：

| 顺序 | 服务 | 阶段 | 配置键（见 `.env.example`） |
|---|---|---|---|
| 1 | MySQL | P0-E3 | `DATABASE_URL` |
| 2 | MinIO / S3 | P1 | `AWS_S3_ENDPOINT_URL`、`AWS_STORAGE_BUCKET_NAME`、`AWS_ACCESS_KEY_ID`、`AWS_SECRET_ACCESS_KEY` |
| 3 | MongoDB | P3 | `MONGODB_URI` |
| 4 | Redis / Celery | 按需，排在 MongoDB 之后 | `REDIS_URL`、`REDIS_KEY_PREFIX`、`CELERY_BROKER_URL`、`CELERY_RESULT_BACKEND`、`CELERY_DEFAULT_QUEUE`、`CELERY_QUEUE_PREFIX` |
| 5 | Elasticsearch | P5 | `ELASTICSEARCH_URL`、`ELASTICSEARCH_INDEX_PREFIX`、`ELASTICSEARCH_READ_ALIAS`、`ELASTICSEARCH_WRITE_ALIAS`、`ELASTICSEARCH_USERNAME`、`ELASTICSEARCH_PASSWORD` |

约束：
1. 各服务使用新站专属的库、桶、前缀、索引和分角色账号，不靠命名约定共享旧站实例。
2. 禁止复用旧站凭据、主机、库名或队列；模板和本目录文件不得提供默认的远端连接地址。
3. 未到阶段的服务保持关闭，不注入凭据、不探活、不启动任务发现；Redis/Celery 总前缀候选也不等于 broker/result 的全链路 ACL 隔离。
4. 真实地址与凭据只放在本地未跟踪的 `.env` 或密钥管理系统中，不得提交。
5. 启用任一服务前，须先完成该阶段的进入条件并取得针对具体目标与操作的授权。
