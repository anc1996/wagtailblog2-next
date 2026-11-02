# WagtailBlog2 守卫测试与装载边界

## 环境与推荐入口

在仓库根目录执行。已核对 WSL2 独占 Conda 环境 `wagtailblog-test`：
Python 3.13.2、Django 6.1.2、Wagtail 8.0.1、modelsearch 1.3.2（2026-11-02 元数据核实）。
这些测试使用标准库 unittest；正式 Home 启动存在下述依赖阻断，不把旧版本记录当成当前通过证据。

```powershell
wsl --exec /root/anaconda3/envs/wagtailblog-test/bin/python -B -m tools.e2_no_io_guard
```

这是专用测试入口：**先安装守卫，再导入 unittest、收集测试和装载 Django/settings**。
入口收集本目录的守卫、Bootstrap、Identity、Resources、Home 及骨架回归合同，先运行守卫探针，再运行项目装载；
收集期有违规或测试失败即非零退出，测试首次失败即停止。
每次验证使用新解释器，不复用已导入 Django/settings/服务客户端的进程。

分别复现时也必须使用新进程：

```powershell
wsl --exec /root/anaconda3/envs/wagtailblog-test/bin/python -B -m unittest discover -s tests -p test_e2_no_io_guard.py -v -f
wsl --exec /root/anaconda3/envs/wagtailblog-test/bin/python -B -m unittest discover -s tests -p test_e2_bootstrap.py -v -f
```

不要用 pytest fixture、测试函数内才安装守卫，或以普通 pytest 收集代替上述入口：
当前 pyproject 的 pytest-django 配置可能在测试模块导入前加载 Django。
若框架、项目或已支持的服务客户端已加载而守卫尚未启用，安装必须拒绝，而不是补装后假称 E2。

## 守卫合同

`tools/e2_no_io_guard.py` 提供 `install_no_io_guard()` 和 `E2IOViolation`。
重复安装活动守卫返回同一实例；`guard.violations` 是累计违规次数，
`guard.events` 仅记录类别与入口名，不保存 URL、连接串、命令参数或凭据。

- 审计出口：socket 创建/连接/DNS 等 `socket.*`，urllib/HTTP，
  sqlite3（包括原生 `_sqlite3` 别名），subprocess、shell、fork/spawn/exec。
- 延迟导入出口：Django 数据库 wrapper 的连接入口；
  Django Storage 及后续子类的读写、删除、列举、路径/URL 等入口。
- 可选客户端：已登记的 MySQLdb/PyMySQL/psycopg/psycopg2/oracledb 连接入口，
  Celery Task/Celery.send_task、Kombu publish。守卫不主动导入这些依赖；
  当前测试用内存模块验证导入边界，**不证明真实客户端或任务服务兼容性**。
- 允许普通本地源码、配置、包元数据读取；安装期间关闭 bytecode 写入。
- `guard.uninstall()` 恢复 Python 补丁、导入 finder 和 bytecode 标志。
  Python 审计 hook 不能移除，卸载后仅留下不执行拦截的 dispatcher。
  只在专用测试/E2 进程使用；这不是 OS 沙箱，不宣称覆盖任意 ctypes/native
  扩展、自定义非 Django Storage 或已有外部资源句柄。

> 范界说明：生产守卫的强制边界是网络、数据库、Django Storage 和任务/进程 IO；它不是操作系统文件的通用 OS 沙箱。测试中的独立安全网额外禁止负向探针写入或删除本地文件，不应将这一测试限制误读为生产守卫已提供完整只读文件系统。
负向探针逐项断言活动状态、异常类型、违规增量及类别；
每个测试额外核对实际违规数与预期探针数，不能吞掉异常后冒充无 IO。
测试模块另装一个不可停用的审计安全网：生产守卫漏拦截时直接令探针失败，
不得实际执行数据库/网络/子进程或本地文件写入。卸载测试只允许临时创建并关闭
一个未连接、未 bind/listen 的 socket，用于确认生产守卫不再影响普通运行时。

## 当前骨架装载：含明确 Mock，不是纯 E2 通过

`test_e2_bootstrap.py` 在活动守卫下验证：

- 当前 settings 的实际源码路径；
- `django.setup()`、项目 URL 路由、WSGI/ASGI application 装载；
- `check` 系统检查及数据库 wrapper 仍没有连接；
- P0-DEV-01 的 `site_identity.User`、P0-DEV-02 的 `resources.Image`、
  `resources.Rendition`、`resources.Document` 和 P0-DEV-03 的 `site_home.HomePage`；
  当前只能在兼容隔离环境下完整装载，项目仍无迁移目录。

**以下能力 Mock 仅在测试内生效：**

1. `modelsearch.backends.database.sqlite.utils.fts5_available = False`：
   当前 modelsearch 在模型导入和系统检查时通过内存 SQLite 建表探测 FTS5。
   守卫不允许 `sqlite3.connect(":memory:")`，因此测试假定 FTS5 不可用；
   系统检查产生的 `modelsearch.W003` fallback 警告被捕获并断言，未冒充真实能力验证。
2. `socket.has_ipv6 = False`（仅 `django.setup()` 范围）：
   urllib3 导入时会创建并 bind IPv6 socket 探测能力；测试假定 IPv6 不可用，
   不让依赖捕获守卫异常后掩盖违规。
3. 默认数据库 features 类的 `supports_json_field = True`（仅 Bootstrap 系统检查）：
   避免 Django 检查 JSONField 能力时打开 cursor；这不证明真实后端支持 JSON。
   测试执行默认 `check` 及单独的 `compatibility` 标签检查。

测试不放行任何上述 IO；装载期间违规增量必须严格为零。
结果属于 **守卫负向验证 + Mock 辅助的当前骨架装载**，
不是未经 Mock 的当前 settings 纯 E2，也不验证 FTS5/IPv6 能力。
已创建并装载最小自定义 User 与公共资源模型，但没有创建项目迁移，
也没有构建/验证项目或第三方迁移图，
更没有验证迁移、真实数据库、Storage、队列、浏览器或真实用户态。
**不得据此宣布完整 P0 E2、P0 已验收或准入 P1。**

## P0-DEV-03 本轮隔离结果（2026-11-02）

PyPI 在 18:20（Asia/Singapore）仍以 8.0.1 为最新稳定版，尚无 8.1 正式发布文件。
本轮旧临时目录已不存在，重新建立 `--system-site-packages` venv，
先用 `pip install --no-deps --only-binary=:all: wagtail==8.1rc1` 做单变量覆盖。
`pip check` 发现 RC 要求 `draftjs-exporter>=7.3.0,<8.0`，正式环境只有 7.1.0，
因此仅在 venv 再覆盖 `draftjs-exporter==7.3.0` 并重跑本节用例。其余依赖复用指定环境。
最终 `pip check` 退出码 1，仅剩项目 metadata 固定 Wagtail 8.0.1 与 RC 的预期冲突；
这不是全依赖解析通过或正式升级验收。正式 Conda、`pyproject.toml` 和原环境 site-packages 均未修改。

在 Home worktree 根目录执行，`RC` 指向本轮隔离解释器：

```bash
RC=/tmp/p0-dev-03-resume-20261102T101852Z/venv/bin/python
PYTHONPATH=src "$RC" -B -m unittest tests.test_home_contract -v
PYTHONPATH=src "$RC" -B -m unittest tests.test_identity_contract -v
PYTHONPATH=src "$RC" -B -m unittest tests.test_resources_contract -v
PYTHONPATH=src "$RC" -B -m unittest tests.test_e2_bootstrap -v
"$RC" -B -m unittest tests.test_e2_no_io_guard -v
"$RC" -B -m tools.e2_no_io_guard
```

分别通过 6、3、9、1、21 项，退出码均为 0；组合入口通过 40 项，退出码 0。
每条独立命令使用新进程。守卫负向测试有预期违规；模型装载和检查新增违规必须为 0，
不能把二者的计数混为“从未触发守卫”。Home 测试额外验证实际父子类型解析、
原生 Page 父链接和方法继承、文档路由、Redirects 配置及 API v3 未挂载。
这不是页面请求、文件交付或真实用户态验证。

同一 `b4436e8` 无 Home 基线的正式/RC runner 均为 25/25，Resources 均为 9/9，退出码 0。
正式 8.0.1 下 Home 为 0 项执行、`setUpClass` 1 error，退出码 5：
`redirects.ready()` 导入 API v3 后构造 `HomePageCreateSchema` 触发 Discriminator 异常。
正式不带 Mock 的守卫 `manage.py check` 退出码 1，先被 SQLite FTS5 探针拦截。
二者属于不同入口的阻断；不得通过跳过测试或放宽守卫消除。

RC 仍有 Django `EMAIL_BACKEND` 弃用提示；本轮不改邮件配置。正式稳定修复须另经隔离验证和批准。
该轮验证时不提交、推送或创建 Home PR；后续 04 U41 已允许功能分支和 Draft PR 审查交付，正式兼容与合并仍阻断。原生日志位于上述 `/tmp/` 证据目录，属于可丢弃材料；
正式摘要以 11 N11 为准。完整迁移图、资源权限策略遗留及 E3 仍未完成。

### 官方脚手架对齐修正

本节追加于上述 40 项历史验证之后。`tests.test_home_scaffold` 检查最小首页模板实际加载、
内存标题转义、已安装 `django_filters` 的模板发现、DEBUG 静态资源路由与全媒体直出移除。
所有路径只作解析，不读取媒体、不执行请求或 Wagtail 页面生命周期。

```bash
PYTHONPATH=src "$RC" -B -m unittest tests.test_home_scaffold -v
"$RC" -B -m tools.e2_no_io_guard
```

模板装载读取本地源码，允许在既有守卫范围内执行；Mock 仍仅限原有能力探针。
开发静态路由不是媒体交付：带扩展名的 `/media/` 原件路径不能落入 Django 直接文件服务。
原生 `/documents/` 保留 Collection 限制检查，不证明其自动继承引用页面的发布状态；
实际图片和私有文档交付分别在 P1、P2a 验证。正式 8.0.1 启动阻断不变；Draft PR 仅按 04 U41 供审查，不代表可合并。

实际结果：修正前 4 项测试出现 5 个失败、2 个 error（含子测试，退出码 1），
修正后 4 项通过；组合入口为 44 项通过，退出码均 0。模板渲染及路由解析新增守卫违规为 0。
正式 8.0.1 执行同一骨架测试仍为 0 项运行、`setUpClass` 1 error、退出码 5。
新证据位于上述临时目录的 `scaffold-*.log` 和 `scaffold-results.json`。

## manage.py 的显式接入与实际阻断

```powershell
wsl --exec /root/anaconda3/envs/wagtailblog-test/bin/python -B manage.py --e2-no-io check
```

该路径在注入 `src`、导入 Django/settings 前安装守卫，只接受精确的 `check`，
不接受其他管理命令或数据库参数；即使命令捕获违规异常，入口仍检查计数并失败。
它**不使用测试中的能力 Mock**。当前环境的预期结果是非零退出：
modelsearch 导入期内存 SQLite 探测触发 `E2IOViolation`。这是已发现的装载阻断，
不是纯 E2 装载通过；不得放宽守卫、清零计数或对该连接加白名单制造绿色结果。

普通 `python manage.py check` 不安装守卫，不能称为无 IO 或完整 E2；
当前已知它可能触发上述内存 SQLite 探测，本轮不应无守卫执行。
普通开发入口的行为保持不变；仅导入 `manage.py` 不启用守卫。

## 静态检查与禁止项

源码语法验证使用 `compile(source, filename, "exec")`，不生成 `.pyc`；
另执行适用的 UTF-8 文档检查、TOML 解析和 `git diff --check`。
语法/格式通过不等于业务或 E2 验收；Git 当前文件若未跟踪，另检查这些文件的行尾空白。

禁止运行 `migrate`、`makemigrations`（包括 dry-run）、`collectstatic`、`runserver`；
禁止真实数据库、MongoDB、Redis、MinIO、Elasticsearch、Celery 等服务访问。
不得 DROP/flush/清库、清桶或删除用户数据。测试执行本身不授权提交或推送 Git；本轮审查交付另获 04 U41 授权。
未来 Page 测试夹具只在专用测试 App 注册，不加入生产模型依赖。

## 本轮异常记录（不是通过证据）

中间一轮启动顺序探针错误地排在正常 finder 后，未截住 Django 导入；
后续卸载/重装失败后测试未停止，出现未拦截的本地 fork/shell、内存 SQLite 和
网络负向探针尝试，不能声称该轮无 IO 或从失败输出排除所有副作用。
已修正 finder 顺序，增加每探针 active 检查、fail-fast 和独立审计安全网。
检查发现遗留零字节文件 `var/media/do-not-log-this_nkJeGZe`；
它不在本轮允许写入/清理范围，保留供主代理或用户审阅处置，未擅自删除。
