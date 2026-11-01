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
