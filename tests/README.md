# WagtailBlog2 守卫测试与装载边界

## 环境与推荐入口

在仓库根目录执行。已核对 WSL2 独占 Conda 环境 `wagtailblog-test`：
Python 3.13.2、Django 5.2.8、Wagtail 8.0、modelsearch 1.3.2。
当前环境未安装 pytest/pytest-django；这些测试使用标准库 unittest，不联网安装依赖。

```powershell
wsl --exec /root/anaconda3/envs/wagtailblog-test/bin/python -B -m tools.e2_no_io_guard
```

这是专用测试入口：**先安装守卫，再导入 unittest、收集测试和装载 Django/settings**。
入口只收集本目录的守卫、身份合同和骨架装载测试，先运行守卫探针，再运行项目装载；
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
- P0-DEV-01 的 `site_identity.User` 与 P0-DEV-02 的 `resources.Image`、
  `resources.Rendition`、`resources.Document` 已装载；项目仍无迁移目录。

**装载有两个显式、仅测试内生效的能力 Mock：**

1. `modelsearch.backends.database.sqlite.utils.fts5_available = False`：
   当前 modelsearch 在模型导入和系统检查时通过内存 SQLite 建表探测 FTS5。
   守卫不允许 `sqlite3.connect(":memory:")`，因此测试假定 FTS5 不可用；
   系统检查产生的 `modelsearch.W003` fallback 警告被捕获并断言，未冒充真实能力验证。
2. `socket.has_ipv6 = False`（仅 `django.setup()` 范围）：
   urllib3 导入时会创建并 bind IPv6 socket 探测能力；测试假定 IPv6 不可用，
   不让依赖捕获守卫异常后掩盖违规。

测试不放行任何上述 IO；装载期间违规增量必须严格为零。
结果属于 **守卫负向验证 + Mock 辅助的当前骨架装载**，
不是未经 Mock 的当前 settings 纯 E2，也不验证 FTS5/IPv6 能力。
已创建并装载最小自定义 User 与公共资源模型，但没有创建项目迁移，
也没有构建/验证项目或第三方迁移图，
更没有验证迁移、真实数据库、Storage、队列、浏览器或真实用户态。
**不得据此宣布完整 P0 E2、P0 已验收或准入 P1。**

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
不得 DROP/flush/清库、清桶、删除用户数据、提交或推送 Git。
未来 Page 测试夹具只在专用测试 App 注册，不加入生产模型依赖。

## 本轮异常记录（不是通过证据）

中间一轮启动顺序探针错误地排在正常 finder 后，未截住 Django 导入；
后续卸载/重装失败后测试未停止，出现未拦截的本地 fork/shell、内存 SQLite 和
网络负向探针尝试，不能声称该轮无 IO 或从失败输出排除所有副作用。
已修正 finder 顺序，增加每探针 active 检查、fail-fast 和独立审计安全网。
检查发现遗留零字节文件 `var/media/do-not-log-this_nkJeGZe`；
它不在本轮允许写入/清理范围，保留供主代理或用户审阅处置，未擅自删除。
