---
name: wagtailblog-dev-workflow
description: WagtailBlog2 新站的风险分级、公共能力合同、隔离测试与证据交付流程。
---

# WagtailBlog2 新站开发工作流

## 范围

先读根目录 `AGENTS.md`、`.codex/AGENTS_INTERACTION_PROTOCOL.md` 和 `说明书/00-产品需求与项目管理/00-README.md`。旧仓库只用于只读功能和风险参考，不能成为新站的代码、迁移、数据库或服务依赖。

## 风险门禁

- 文档和配置任务做最小修改，验证 UTF-8、链接、格式和配置语法；不因此运行数据库或服务。
- 身份、权限、Revision、发布/删除、外置正文、Outbox、迁移及跨存储事务先完成权威、提交点、幂等、锁序、失败和恢复合同，再实现。
- 数据库迁移、建库、批量修复、物理删除和生产访问需要用户明确授权。

## 生命周期合同

- Wagtail 原生 Page、Revision、Workflow、预览、排程、发布、恢复和页面树操作是权威。
- MongoDB 只保存声明字段的不可变外置版本；GuidePage 首版 body 必须外置。SQL 正式指针、业务状态和 Outbox 在同一 SQL 事务提交。
- 搜索是可重建投影，不决定发布；共享资源的删除和回收与页面删除分开。
- 公共能力不导入 BlogPage/GuidePage；具体页面关系按原生 ParentalKey/Revision 保存。

## 验证与报告

区分静态检查、E2 无外部 IO、Mock/隔离服务、浏览器和真实用户态证据。骨架阶段可执行 Python 语法、TOML 解析、Django `check`、入口导入、文档链接和 `git diff --check`；不得执行 `migrate`、`makemigrations`、`collectstatic`、真实服务连接或生产命令。

每个切片都更新 `说明书/00-产品需求与项目管理/11-新站实施进度与验收台账.md`。正式方案未同步或证据不足时，验收状态保持“未验收”。
