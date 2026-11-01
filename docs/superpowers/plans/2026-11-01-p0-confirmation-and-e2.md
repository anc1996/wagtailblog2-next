# P0 产品确认与 E2 无外部 IO 验证实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 登记 U27～U36 产品确认，收紧 P0 合同和责任链，并建立可验证的导入前无外部 IO E2 守卫。

**Architecture:** 保留现有新站方案，只做增量文档同步和最小 E2 基础设施。产品确认与治理文档由 Terra/Sol 分工维护；E2 守卫在 Django/settings 导入前阻断数据库、网络、Storage、任务投递和子进程，并用负向探针验证阻断有效。当前未获用户明确接受的持久身份和媒体模型只作为 Sol 推荐，不得伪装成已批准迁移合同。

**Tech Stack:** Python 3.13、Django 5.2、Wagtail 8.0、pytest/pytest-django（仅无外部服务验证）。

**Spec:** `说明书/00-产品需求与项目管理/04-需求确认记录与下一轮决策清单.md` 的 U27～U36 草案、ADR-P0-01～08、`AGENTS.md` 与 `.codex/AGENTS_INTERACTION_PROTOCOL.md`。

## Global Constraints

- 不修改旧仓库 `F:\openclaw\workspace\wagtail\wagtailblog2` 或旧生产项目 `E:\source\python\python_Web_Development\demo\wagtail\wagtailblog3`。
- 不执行 `migrate`、`makemigrations`、`collectstatic`、`runserver`，不连接 MySQL、MongoDB、Redis、MinIO、Elasticsearch、Celery 或任何真实服务。
- 不提交、不推送、不部署、不清理现有未跟踪文件和 `__pycache__`。
- 普通公开图片和附件按局域网产品政策保持简单交付；后台、草稿、未发布和私有资源仍须保护。
- E2 的“无外部 IO”只允许本地源码、配置和元数据读取；任何数据库、网络、Storage、任务或子进程越界都必须失败。
- 没有用户明确接受的持久 App label、`AUTH_USER_MODEL`、资源模型设置和迁移路线，不得标记模型/迁移合同已批准。

---

### Task 1: 产品需求与治理文档同步

**Files:**
- Modify: `AGENTS.md`
- Modify: `.codex/AGENTS_INTERACTION_PROTOCOL.md`
- Modify: `.codex/agents/terra.toml`
- Modify: `.codex/agents/sol.toml`
- Modify: `.codex/agents/gemini.toml`
- Modify: `说明书/00-产品需求与项目管理/00-README.md`
- Modify: `说明书/00-产品需求与项目管理/01-统一外置内容与公共能力产品需求基线.md`
- Modify: `说明书/00-产品需求与项目管理/02-统一外置内容与公共能力项目管理路线图.md`
- Modify: `说明书/00-产品需求与项目管理/04-需求确认记录与下一轮决策清单.md`
- Modify: `说明书/00-产品需求与项目管理/08-图片公共能力第一批脱离方案.md`
- Modify: `说明书/00-产品需求与项目管理/09-新网站产品与公共能力架构重建方案.md`
- Modify: `说明书/00-产品需求与项目管理/11-新站实施进度与验收台账.md`

**Interfaces:**
- Consumes: 用户已确认选择 `1A、2A、3B、4A、5C、6C、7B、8A、9A、10A`。
- Produces: U27～U36 正式记录；局域网访问和简化公开资源交付合同；角色职责统一；P0/E2/E3 状态准确；I0 使用根 `manage.py` 和 `src/wagtailblog2/...`。

- [ ] **Step 1: 检查 U27～U36 是否占用**

运行：

```powershell
rg -n "U2[7-9]|U3[0-6]" "说明书/00-产品需求与项目管理/04-需求确认记录与下一轮决策清单.md"
```

预期：确认没有既有同编号记录；如已占用，使用下一个连续编号并在报告中说明。

- [ ] **Step 2: 写入十项确认及阶段边界**

在 04 中新增 U27～U36，明确“需求已确认不等于实现或验收”，并保留未决的普通实现细节。

- [ ] **Step 3: 同步受影响正式文档**

只更新实际受影响段落：01 产品基线、02 路线和阶段门禁、08 I0 与资源交付原则、09 架构与权限/统计/备份合同、00 入口摘要、11 台账。

- [ ] **Step 4: 同步角色和验证门禁**

统一 Terra 主控调度与验收、Sol 首席架构师、Gemini 工程实现、独立 Reviewer 高风险复核；明确普通 `manage.py check` 不等于 E2。

- [ ] **Step 5: 运行文档静态检查**

检查 UTF-8、空白和相对链接；不得把本切片写成代码完成或已验收。

### Task 2: P0 E2 导入前无外部 IO 守卫

**Files:**
- Create: `tools/e2_no_io_guard.py`
- Create: `tests/test_e2_no_io_guard.py`
- Modify: `tests/README.md`
- Modify: `manage.py`

**Interfaces:**
- Produces: `install_no_io_guard()`，在 Django/settings 导入前安装；违规操作抛出明确的 `E2IOViolation`；守卫提供可查询的违规计数供测试断言。
- Consumes: Python 标准库 socket、subprocess、sqlite3、urllib/HTTP 出口和项目启动入口。

- [ ] **Step 1: 写失败测试**

测试必须在导入项目 settings 前验证：

```python
def test_guard_blocks_socket_and_records_violation():
    guard = install_no_io_guard()
    with pytest.raises(E2IOViolation):
        socket.create_connection(("127.0.0.1", 9), timeout=0.01)
    assert guard.violations == 1
```

另覆盖 sqlite3 连接、子进程启动和 HTTP/URL 出口；允许普通本地文件读取。

- [ ] **Step 2: 运行测试确认失败**

```powershell
python -m pytest tests/test_e2_no_io_guard.py -q
```

预期：因守卫模块或接口不存在而失败。

- [ ] **Step 3: 实现最小守卫**

守卫必须在项目导入前安装，阻断并计数数据库、网络、Storage 后端调用和任务/子进程出口；不得依赖 pytest fixture 在 Django 导入后才生效。实现不得连接真实服务或读取凭据。

- [ ] **Step 4: 接入安全启动路径**

让受 E2 验证的启动路径先安装守卫，再插入 `src` 并加载 settings；保留普通开发入口的明确边界，不将普通 `manage.py check` 宣称为完整 E2。

- [ ] **Step 5: 运行守卫测试和基础静态检查**

```powershell
python -m pytest tests/test_e2_no_io_guard.py -q
python -m py_compile manage.py tools/e2_no_io_guard.py
```

### Task 3: E2 受守卫装载与合同门禁复核

**Files:**
- Create/Modify: `tests/test_e2_bootstrap.py`
- Modify: `tests/README.md`
- Modify: `说明书/00-产品需求与项目管理/11-新站实施进度与验收台账.md`

**Interfaces:**
- Consumes: Task 2 的 `install_no_io_guard()` 和当前 `wagtailblog2.settings.dev`。
- Produces: 受守卫装载结果、实际模块来源、AppConfig 清单和“持久身份尚未批准/模型尚未建立”的明确证据。

- [ ] **Step 1: 写受守卫装载测试**

验证 setup、settings、URL、WSGI/ASGI 导入，并断言：

- 没有数据库、网络、Storage、任务或子进程违规；
- 当前骨架没有自定义 User、资源模型或迁移图；
- 不能将该结果标为完整 P0 E2。

- [ ] **Step 2: 运行失败测试并修复最小装载问题**

```powershell
python -m pytest tests/test_e2_bootstrap.py -q
```

只修复当前 E2 装载所需问题，不创建业务 Page、Mongo bridge、Outbox 或真实迁移。

- [ ] **Step 3: 在守卫下执行受限验证**

允许读取 Python 源码、配置和已安装包元数据；禁止数据库连接、网络请求、Storage 访问、任务投递和迁移执行。

- [ ] **Step 4: 登记证据和阻断条件**

在 11 号台账区分：守卫验证通过、当前骨架装载通过、User/媒体模型和迁移图尚未建立或未获身份合同批准。
