# ADR-P0-02：Python 根包与 AppConfig 所有权

- 日期：2026-10-31
- 状态：P0-DEV-01 身份 AppConfig 已批准并实现；资源与首页 App 身份已由 U38 确认，测试夹具 App 仍为后续候选。
- 证据级别：E2 无外部 IO 身份装载已验证；完整迁移图和真实服务尚未验证。
- 用户批准：身份、resources/site_home App 身份已批准；模型装载、迁移图和真实服务仍未验证。

## 来源与用户已确认

依据旧参考仓库 `说明书/00-产品需求与项目管理/` 的 00、04 U12/U24/U26/U37/U38、08、09 §10.2 和 10 §12～14。独立仓库、最小 AbstractUser、`wagtailblog2` 根包及 `resources`/`site_home` App 身份已确认；其余实现和迁移证据仍需门禁验证。

本轮补充确认 resources、site_home App 身份和迁移路线 B；测试夹具 AppConfig 仍为后续候选。统一采用根 `manage.py` 与 `src/wagtailblog2/` 的文档路径口径，E2 证据仍不等于真实迁移或服务验收。

## 当前事实与未验证项

新仓库已有 `src/wagtailblog2/`、最小 settings、启动入口和身份 AppConfig；身份装载已在导入前守卫下验证。resources 与 site_home 身份已确认但尚未实现；测试夹具 AppConfig、打包安装、完整迁移图、真实权限和服务仍未验证。

## 已批准身份实现与后续候选

采用 `src/wagtailblog2/` 为唯一产品 Python 根包；仓库名 `wagtailblog2-next` 不作为含连字符的导入名。身份行是当前实现，其余行仍是后续候选。

| 责任 | AppConfig 类候选 | name 候选 | 持久身份 |
|---|---|---|---|
| 认证身份 | `wagtailblog2.apps.identity.apps.IdentityConfig` | `wagtailblog2.apps.identity` | P0-DEV-01 已批准并实现 |
| 公共资源 | `wagtailblog2.apps.resources.apps.ResourcesConfig` | `wagtailblog2.apps.resources` | U38 已确认身份；见 ADR-P0-03/04 |
| 首页 | `wagtailblog2.apps.home.apps.HomeConfig` | `wagtailblog2.apps.home` | U38 已确认身份；随阶段启用，不提前做全部编排 |
| 图片测试夹具 | `wagtailblog2.tests.resource_fixtures.apps.ResourceFixturesConfig` | `wagtailblog2.tests.resource_fixtures` | 仅测试附加 App |

`wagtailblog2.content` 承载 Registry/Access/Selection/Card 等公共协议；`wagtailblog2.content_blocks` 承载公共 Block/渲染组件。没有持久模型时不分配 App label，不为每个 Provider 建 Django App。

根级 `tests/` 可放测试入口和断言；需要迁移的夹具 App 按上表固定导入身份，避免测试路径覆盖产品包。根级 `config/` 的职责建议仅为部署/工具配置资料，Django settings 放产品根包内，详见 [ADR-P0-06](ADR-P0-06.md)；该布局同样待审定，不移动现有他人文件。

## 依赖与导入合同

1. 业务 Page/可选 App → 公共接口 → Django/Wagtail；公共接口不导入 BlogPage/GuidePage，也不通过类型分支隐藏反向依赖。
2. 装配层允许显式注册具体模型；页面自己的 ParentalKey/Orderable 子关系允许指向具体 Page，以保留原生 Revision。
3. 根 `__init__` 不自动导入 Celery、settings、旧站包或连接客户端。AppConfig/ready/hooks 的装配仅做受控本地注册，不发外部请求、不主动扫描业务数据。
4. 旧新 resources 包不得同时安装；不得把旧仓库目录加入 sys.path 解决缺失导入。
5. external_content、people、正式 search、blog、guides 为后续业务边界，不由本 ADR 提前创建其 AppConfig 或批准其 label。
6. 生产模型不得依赖 `resource_fixtures`；测试和未来正式复用同一产品迁移历史。

## 备选方案与待用户批准决定

- **推荐** `src/wagtailblog2/`：区分仓库名与导入名，便于隔离旧根包；需同步打包/工具路径，不能只建目录。
- 备选仓库根平铺包：配置较少，但须另验当前目录遮蔽导入等问题；不能在不同环境混用两套根包。
- 待后续确定：测试夹具位置、顶层 config 的职责和 App 的实际装载时机；根包、src 布局、身份、resources/site_home App 身份不再作为待用户选择。
- 不选整体复制旧 `wagtailblog3`：其历史导入耦合与任务发现不满足新站边界；这是历史源码风险，不声称本批观察到网络连接。

## 风险与依赖

依赖 [ADR-P0-03](ADR-P0-03.md) 的持久 label 和 ADR-P0-06 的入口隔离。包改名会影响配置、历史迁移导入路径及序列化可调用对象；label 改名是另一类持久身份变化，不可混为普通文件移动。原型中偷装旧业务、把夹具变成正式父依赖会污染迁移图。

## 验证计划、停止与回退

- E1：静态核对已确认全限定路径与 ADR-P0-03/06/07 一致；最小骨架已建立，resources/site_home AppConfig 尚未实现。
- E2：在获批实施范围内，项目导入前阻断 DB、网络、Storage、任务和子进程，受守卫检查模块来源、AppConfig.name/label、重复模型/反向关系、ready/hooks/URL/模板/static/Storage/任务发现；不生成或执行迁移、不连真实服务、不开展 E3，禁止靠删必要 App 让测试通过。
- E3：具体授权后验证打包入口、原生后台及 chooser；无 IO 导入结果不证明这些功能。
- 停止：根包争议、重复 label、旧包被解析、夹具反向进入生产图或导入发生 IO。
- 回退检查：未迁移原型可按文件所有权撤回本批改动；持久化后的 Python 路径/label 不随意更名，保留历史可解析入口，另审兼容方案。不执行覆盖 reset 或清理他人文件。

## P0-DEV-02 实施记录（2026-11-02）

- 已实现 `wagtailblog2.apps.resources.ResourcesConfig`，持久 `label=resources`；`resources.Image`、`resources.Rendition`、`resources.Document` 已按 Wagtail 8.0.1 抽象模型建立。
- 已在 settings 激活 `WAGTAILIMAGES_IMAGE_MODEL="resources.Image"` 与 `WAGTAILDOCS_DOCUMENT_MODEL="resources.Document"`，未引入业务 Page 或旧站资源。
- 受导入前无外部 IO 守卫的定向装载与模型合同测试已通过；这只证明当前原型装载边界，不证明迁移或真实服务验收。
- 本节覆盖此前“resources 尚未实现”的当前状态表述；历史记录保留，迁移文件、完整迁移图和 E3 仍未完成。

## P0-DEV-03 实施记录（2026-11-02）

- 已建立 `wagtailblog2.apps.home.apps.HomeConfig`，固定 `label=site_home`，并在项目 settings 注册。
- `site_home.HomePage` 已作为无额外业务字段的 Wagtail `Page` 子类加入；未覆盖原生生命周期，也未限制未来子页面类型或创建位置。
- Home 模型/Bootstrap 测试目前被 Wagtail API 页面 schema 启动错误阻断，尚不能据此确认模型注册和完整受守卫装载通过；无迁移文件、无 Site/Locale 数据，未连接真实服务。
- 本节覆盖此前“site_home AppConfig 尚未实现”的历史状态；完整 E2、迁移图和 E3 仍未完成。

### 恢复验证增量（2026-11-02，04 U40）

- 本节覆盖上面首次启动失败时的验证状态：Home、Identity、Resources、Bootstrap 及守卫合同在独立 Wagtail 8.1rc1 venv 下通过；正式 8.0.1 仍启动失败。完整命令、Mock 和数量见 11 N11。
- 当前不启用 `wagtail.api.v3`；未来自定义业务 API 优先 DRF，不替换 Wagtail 后台内部接口。本轮只登记边界，不新增 API 或改变正式依赖。
- 保留 Wagtail 原生 Redirects、Documents、Locale；禁止以删 App、覆盖框架生命周期或虚假 Page 规避启动问题。模型身份、迁移 B 与 E3 门禁不变；隔离通过不等于正式兼容或验收。

### 官方初始化对齐增量（2026-11-02）

- 保留已确认的 `src` 布局和 App label；按官方模板补注册现有 `django_filters`，Home 模板使用原生 label 推导路径 `site_home/home_page.html`。
- 开发静态资源路由先于 Wagtail 兜底；不采用示例的全媒体目录直出，避免绕过草稿/私有资源边界。原生文档路由保留，公共图片交付仍属 P1。
- 官方 8.0.1 原版脚手架在同一守卫/Mock 条件下也复现启动错误；本次配置修正不关闭正式依赖兼容门禁，不生成迁移或初始化数据。测试证据见 11 N11。
