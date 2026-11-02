# P0-BLOCKER-01：启动兼容修复隔离验证

日期：2026-11-02。输入：Home 分支实现及台账提交 `d41d2f8694766d68a30970acaa51c61b6b10ebde`。
**结论：8.0.1 最小回移构建已解决隔离环境的启动错误；正式环境尚未替换，P0-DEV-03 未验收。**

**交付增量（U43）**：用户随后要求完成增量必须推送。成功补丁、可重跑的额外合同测试和操作说明纳入[仓库验证附件](../../tools/compat/wagtail_8_0_1/README.md)，沿用 Draft PR #4 供远程审核。文末“不提交、不推送”保留为此前隔离验证阶段历史，已由 U43 覆盖；正式依赖和环境仍未变更。

## 官方版本与实际修复

- 本轮 PyPI JSON 核实最新稳定版仍为 **8.0.1**，发布于 2026-10-20；它没有以下启动保护。官方 sdist SHA256：`819865a10bce86b16288cfaefa4195b90ffb5e7ac494fb18659e7be099ef386f`。
- `19ea8b53a660ef65d0e275a03c05dea6118c2f82` 保护 Redirects、Documents、Locales、Snippets。四文件候选 `.1` 实测仍失败，完整栈转到 Images，不能宣称该提交单独解决 8.0.1。
- Images 的上游保护在它的直接父提交 `123e88ddd5f73378f73ed5c4ce6dc234425db0d0`。最终构建 **`8.0.1+wb2next.apiv3guard.2`** 仅移植五个 AppConfig 中已有 API 尾段的 `apps.is_installed("wagtail.api.v3")` 条件，不带入后续 ImageBlock、EmbedBlock 或缓存功能。
- 实际源码差异为 `wagtail/{contrib/redirects,documents,images,locales,snippets}/apps.py`，另有 `wagtail/__init__.py` 的测试版本标识。条件外的权限、信号、chooser、Revision 比较、display、ReferenceIndex 等原生代码逐字保留。
- 与官方 wheel 比较：4,251 个 `wagtail/` 载荷文件仅上述六文件不同，无增删；`Requires-Dist` 与 `Requires-Python` 完全相同。测试 wheel SHA256：`0a593d987088d3f8ab4a4ca8fae097b61fa931701c6f556542dbcf1f9ca1a5b5`。这是本次测试产物的哈希，不承诺其他重建的 ZIP 时间戳相同。

官方来源（已保存 GitHub API 返回及教程 Git blob，不只依据 Changelog）：

```text
https://pypi.org/pypi/wagtail/json
https://github.com/wagtail/wagtail/commit/19ea8b53a660ef65d0e275a03c05dea6118c2f82
https://github.com/wagtail/wagtail/commit/123e88ddd5f73378f73ed5c4ce6dc234425db0d0
https://api.github.com/repos/wagtail/wagtail/contents/docs/getting_started/tutorial.md?ref=v8.0.1
```

## 官方教程与脚手架对照

使用正式 8.0.1 的实际 `wagtail start` 入口在临时目录生成 29 个文件，退出码 0；未修改生成结果。官方项目与新站在相同能力 Mock 下都复现 Schema 异常。教程按 v8.0.1 Git blob `0d11b2f83bcf2584b3d3e452fddfc73813da40a7` 核实；其中迁移、建用户、运行服务器步骤未执行。

| 项目 | 官方默认 | 新站与差异原因 | 本轮处理 |
|---|---|---|---|
| INSTALLED_APPS 顺序 | home/search 在前，共享 Wagtail/Django 组件在后 | identity/resources/home 在前，共享组件相对顺序一致；已有 django_filters | 无需重排；不加入示例搜索或 API |
| MIDDLEWARE | 8 项，含认证、CSRF、RedirectMiddleware | 完全相同 | 保留 |
| TEMPLATES | DjangoTemplates、APP_DIRS、4 个 context processor | 等价，目录按 src 布局调整 | 无需修改 |
| URL | 管理、文档、示例搜索，Page 兜底最后 | 原生管理/文档和末尾 Page 保留，无示例搜索/API | 无需增加路由 |
| HomePage/模板 | 最小 Page 子类及欢迎模板 | 最小原生 Page、site_home 模板、转义中文标题 | 身份合同不同，保留现有实现 |
| 静态资源 | DEBUG staticfiles 路由 | 同一方式，已位于 Page 之前 | 保留 |
| 开发媒体 | DEBUG 下直出整个 MEDIA_ROOT | 新站移除直出，防止私有原件绕过授权 | 不照搬官方演示配置 |
| Documents/Images | 默认资源模型，原生 Collection 策略及注册 | 自定义 resources 模型，使用相同原生策略；注册已隔离验证 | 只修依赖启动；交付权限仍待 E3/P1/P2a |
| Redirects/Snippets | 原生权限及信号注册 | 同一原生链，候选构建保留非 API 注册 | 不删除功能、不重写生命周期 |
| Site/Locale | 原生模型；未安装可选 Locales 管理 App；官方数据迁移创建首页/Site | 新站不初始化数据，持久身份及迁移 B 已确认 | 不复制官方迁移；辅助进程单独装载 Locales 验证 |
| 用户/权限 | 默认 User 和原生组、权限 | 最小 site_identity.User(AbstractUser)，原生关系保留 | 不改回默认 User，不造第二套权限 |
| 上传与其他设置 | 显式文档类型/10MiB 限制、字段数上限、英文/UTC 等 | 新站中文/独立路径；上传类型、大小尚待阶段合同 | 上传启用前补齐；不是当前启动根因，不扩改本轮 |

## 实际命令与结果

实验根目录 `R=/tmp/p0-blocker01-n_l7qs3n`，额外测试目录 `S=/tmp/p0-blocker01-scaffold-50_8o7x5`。
构建使用独立 build venv（setuptools 80.9.0）；候选运行 venv 通过 `--system-site-packages` 只读复用正式依赖，仅覆盖自己的 Wagtail。正式 Conda 未改。

在 Home worktree 执行：

```bash
C=/tmp/p0-blocker01-n_l7qs3n/candidate2-env/bin/python
S=/tmp/p0-blocker01-scaffold-50_8o7x5
"$C" -B -m tools.e2_no_io_guard
PYTHONPATH=src "$C" -B -m unittest tests.test_home_contract -v
"$C" -B "$S/test_startup_compatibility.py"
"$C" -B "$S/test_startup_compatibility.py" --locales
"$C" -B /mnt/c/Users/haryk/AppData/Local/Temp/p0-blocker01-startup-check.py
"$C" -B -m pip check
```

| 验证 | 结果 | 退出码 |
|---|---|---:|
| 正式 8.0.1 Home RED | 0 项执行、1 个 setup error，原 Schema 异常 | 5 |
| 四 App 候选 `.1` RED | 同类异常，入口已转为 Images；组合 21 探针通过后启动失败 | 1（组合）/5（Home） |
| 五 App 候选 `.2` 组合 | 44/44：Home6、Identity3、Resources9、Bootstrap1、负向探针21、scaffold4 | 0 |
| 单独 Home 回归（重复验证，不累加计数） | 6/6 | 0 |
| 额外兼容合同，默认项目配置 | 20/20，0 失败、0 error、0 跳过 | 0 |
| 同一额外合同，临时加入 Locales 的另一进程 | 20/20；同一组用例的第二种配置，不称40个独立用例 | 0 |
| 独立 startup/check 脚本 | django.setup、默认 check（0 issues）、WSGI/ASGI 装载成功，无请求 | 0 |
| pip check | No broken requirements found | 0 |
| 149 个已安装包约束审计 | 当前启用的 Requires-Dist、Requires-Python 违规 0 | 0 |

Mock 仅为既有 FTS5 不可用、IPv6 不可用；默认系统检查另假定 JSONField capability=True。没有 Mock Schema、API、权限策略或信号注册。组合的43次守卫事件来自预期负向探针；启动及额外合同新增违规0、所有连接保持 None。

额外测试读取真实 policy/receiver/registry，验证五个 App 的非 API 注册、Document/Image 的 Collection/owner 策略、引用索引、图片 chooser/Revision 比较、Rendition 清理、原生 Site/Locale/User 关系；不发送写库信号。API v3 未安装，其 API 主模块未导入，完整路由树未挂载 v3/Ninja；不验证主动启用 API v3 的业务行为。

约束审计另追踪209条当前依赖边及传递启用的 `Willow[heif]`，违规0。`pip check` 不激活项目可选 `services` extra。其中 mysqlclient 实装2.2.7、声明2.3.0仍是 E3 前置差异；其余已核对可选服务/测试依赖满足声明。因此不能声称 MySQL 驱动或所有可选服务已验收。

## 采用建议、待批准操作与回退

**建议短期采用这份有来源、版本和哈希的最小回移补丁，稳定版包含同等修复并通过验证后再替换。** 不采用 RC、不改 Page、不启用 API v3。补丁仍由项目维护，不能冒充官方8.0.1或全量上游修复。

本轮只验证，不安装到正式环境。下一步须用户单独批准以下精确范围：

1. 隔离补丁、来源/哈希及兼容测试已按后续 U43 纳入现有 Home 分支的审查附件；正式采用另行审批。采用时将 `pyproject.toml` 的 Wagtail 精确锁定改为 `8.0.1+wb2next.apiv3guard.2`，指定经过核对的 wheel 获取位置，不能只改版本让 pip 猜来源。原 `==8.0.1` 也接受本地版本，无法区分官方包和修复包，故必须显式固定工件。
2. 仅在正式 `wagtailblog-test` 替换 Wagtail 一个包：从已测试 wheel 以 `pip install --no-deps --force-reinstall <wheel>` 安装；不更新其他包，不改系统软件、不触碰数据库。安装前再次校验上述 SHA。
3. 重跑本报告的默认/额外合同及 pip check；正式兼容通过后才能继续 Home PR 的远程验收流程，不自动合并。
4. 失败时以 `pip install --no-deps --force-reinstall <原官方8.0.1 wheel>` 回退该包，并在功能分支恢复依赖声明；不 reset/force。原官方 wheel SHA256 为 `1e6ad5c7891a54efce1400e168298b5a2cc343b642cee89c31bf5ec30c98b26c`。回退恢复的是已知存在启动 Bug 的原基线，不能称为恢复可运行版本。

没有数据/迁移变化，回退无需数据库恢复。真实空库迁移、权限数据、后台登录/Workflow/发布、Redirect执行、上传/下载、浏览器及完整 P0 E2/E3 均未验收；无 Mock 的守卫启动仍会先拦截 modelsearch 的内存 SQLite 能力探针，这是另一项 E2 装载边界，不能归为本次 Schema 修复失败或偷偷放行。

## 证据与保护状态

### U43 仓库附件交付复验

在现有候选环境中重新运行，以下命令均退出 0：

```bash
C=/tmp/p0-blocker01-n_l7qs3n/candidate2-env/bin/python
"$C" -B -m tools.e2_no_io_guard
"$C" -B tools/compat/wagtail_8_0_1/test_startup_compatibility.py
"$C" -B tools/compat/wagtail_8_0_1/test_startup_compatibility.py --locales
"$C" -B -m pip check
```

组合44/44；额外同组20项在默认与Locales两个新进程分别20/20，无失败、跳过或新增守卫违规。Mock范围同上。发布补丁与原成功补丁逐字节相同；对SHA校验后的原始sdist在新临时目录执行`git apply --check`及`git apply`均成功，应用后全部Wagtail载荷与已测wheel相同。未重新构建wheel，也未执行附件README的安装示例。

交付检查：11个文件UTF-8/无BOM、30个Python语法、6个TOML、6个相对链接、13个Markdown表格及`git diff --check`通过；高置信凭据模式扫描无命中。补丁保持原始unified diff上下文空白，以适用性校验验证，不改写其哈希；`.gitattributes`仅为这一份补丁设置`whitespace=-blank-at-eol`，不改变源码/文档空白检查或E2守卫。正式环境与主目录六项/stash保护再次核对通过。审查入口沿用Draft PR #4，提交及推送以远程PR实际SHA核验，不构成正式安装或合并许可。

本轮独立Reviewer只读复核交付文件，确认无交付阻断；独立复跑仓库额外测试，默认/Locales各20/20，退出0、零跳过/违规。Reviewer未重复构建、载荷比对、组合44项或正式环境保护审计；这些证据由主代理执行。正式采用与Home验收仍待批准。

### 此前隔离验证阶段归档

完整补丁、已测/回退 wheel、官方归档、源码来源、逐命令日志、额外测试和依赖/载荷审计归档于：
`F:/openclaw/workspace/wagtail/artifacts/P0-BLOCKER-01-20261102`。该目录是本地实验附件，不是正式依赖来源承诺，不上传 wheel 或发布 Release。
实际代码差异为其中的 `evidence/wagtail-8.0.1-api-v3-startup-v2.patch`；文件校验清单为 `SHA256SUMS.json`。

独立 Reviewer 只读审查源码与 wheel，独立重跑额外两种配置各20/20通过，确认非API逻辑保持、载荷和RECORD一致，未发现本次隔离补丁的代码阻断。正式工件锁定/安装授权仍是采用门禁，主动启用API v3和真实数据库行为不在结论范围。主代理亦独立重跑额外两种配置；代理返回不代替本会话执行证据。
主目录六项文件哈希、diff/index/HEAD、原stash均未变；正式 Wagtail 的4,251个载荷与官方wheel逐字节一致。Draft PR #4仍开放且为Draft，本轮未提交、推送或合并实验补丁，未连接真实服务或启动业务切片。
