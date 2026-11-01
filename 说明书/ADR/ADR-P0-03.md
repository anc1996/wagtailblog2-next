# ADR-P0-03：正式 App Label 与持久模型身份

- 日期：2026-10-31
- 状态：身份标识已批准用于 P0-DEV-01；资源、首页和测试夹具标识仍为候选。
- 证据级别：E2 无外部 IO 装载已验证；无 ContentType、权限或迁移执行证据。
- 用户批准：`site_identity.User` 身份方案已确认；独立技术审查：本切片待复核。

## 来源与用户已确认

依据旧参考仓库 `说明书/00-产品需求与项目管理/` 的 00、04 U17/U24/U26、08、09 §10.1～10.2、10 §12～14。已确认独立仓库及最小 AbstractUser 方向；本切片进一步固定身份 label 和模型标识。资源模型、迁移路线和首次迁移依赖仍需单独审定。

U27～U36 本身不替代持久身份批准；本轮用户已另行批准 `site_identity.User` 作为 P0-DEV-01 身份实现。`resources` 及迁移 B 仍为技术推荐；E2 仅验证装载，不代替迁移或真实权限验收。

## 已批准身份与后续候选 label 清单

| AppConfig（省略共同根 `wagtailblog2`） | label 候选 | 模型标识候选 | 所有权及边界 |
|---|---|---|---|
| `.apps.identity.apps.IdentityConfig` | `site_identity` | `site_identity.User` | P0-DEV-01 已批准并实现；首个迁移仍待生成/验证 |
| `.apps.resources.apps.ResourcesConfig` | `resources` | `resources.Image/Rendition/Document` | 公共资源，不归 Blog；保持旧方案中 resources 候选，不同时安装旧实现 |
| `.apps.home.apps.HomeConfig` | `site_home` | `site_home.HomePage` | 首页 Page；按阶段实现业务 |
| `.tests.resource_fixtures.apps.ResourceFixturesConfig` | `resource_fixtures` | `resource_fixtures.ResourceArticleTestPage`、`resource_fixtures.ResourceGuideTestPage` | 仅图片测试，不是正式 Blog/Guide |

以上 AppConfig.name 以 [ADR-P0-02](ADR-P0-02.md) 的完整路径为准；label 不由包名末段隐式决定。推荐显式声明，以免 identity/home 等通用名称与依赖包冲突。

纯协议包 content/content_blocks 暂无 label。external_content、people、blog、guides 及公共搜索的最终 label **未在本 ADR 定案**；有持久模型时再形成自有清单，不用 Registry 的 type_key 代替 Django label。

## 持久身份合同

1. label 参与模型解析、默认表名、ContentType、迁移依赖、权限全名及序列化引用；首次迁移后按持久接口管理。
2. `resources.Image` 等写法是模型标识，不是 Python 导入路径，也不单独声明数据库实际表已存在。
3. 保留 Django/Wagtail/第三方 label 与迁移历史，包括原生 `wagtailcore.Page`；不为“统一前缀”批量改写框架身份。
4. 自有 label 的变更会影响 `app_label.codename` 权限全名；裸 codename 是否变化由模型名/权限定义决定，不能一概声称全部变化或自动继承旧权限。
5. 审核 User、Collection、FK、ParentalKey、related_name、chooser、原生 get-model 解析和 ContentType 的一致性，不只检查字符串唯一。
6. 测试与未来正式使用相同生产模型迁移历史；fixtures 只是附加图，生产不得依赖它。
7. `MIGRATION_MODULES` 仅改变迁移来源，不隔离 models/ready/hooks/signals；置为 None 也不是权限或 IO 安全措施。

## 备选、风险与依赖

推荐迁移 B：独立 settings、App 所有权及必要自有 label，详见 [ADR-P0-07](ADR-P0-07.md)。迁移 A 的同 label/新迁移模块只作有条件备用；已确认的独立“仓库 A”不等于选择该技术方案。

不选复用旧 Blog 的模型身份：会继续把资源/人员绑定到特定业务。不选为每个协议分配 App：增加迁移与装载面而未带来数据所有权。

主要风险为双资源包导致重复 label、权限泄漏或迁移历史冲突；改包名误改 label；已生成迁移后继续漂移标识。依赖 ADR-P0-02、[ADR-P0-04](ADR-P0-04.md)、[ADR-P0-05](ADR-P0-05.md) 共同审定。

## 待用户批准决定与未验证项

- 批准或调整四个候选 label、对应配置类/模型名及资源/User 设置值；不重复询问已确认的最小 AbstractUser 方向。
- 同意生产图不依赖测试夹具、第三方身份保持原样及后续 label 另审的边界。
- 未验证：实际 App registry、模型状态、默认表名、ContentType 与权限生成、反向关系、原生 chooser 和各依赖版本兼容性。

## 验证计划、停止与回退

- E1：交叉检查八份 ADR 中 label、模型设置及迁移节点无冲突，不声称已生成任何模型。
- E2：在获批原型范围内，项目导入前阻断 DB、网络、Storage、任务和子进程，受守卫列实际 AppConfig/name/label/model，审阅已有状态、关系和 swappable 解析；不生成或执行迁移、不连真实服务、不开展 E3，静态预期权限不能记为真实创建结果。
- E3：另获具体隔离空库操作授权后，检查真实 ContentType/权限、迁移历史、后台模型选择与 chooser；保留目标及版本证据。
- 停止：重复 label、未批准身份、旧历史混入、权限误绑定或生产依赖 fixtures。
- 回退检查：迁移前修订提案/本人原型；迁移后身份变化必须新专项迁移与授权，不改已应用迁移、不 fake、不删 ContentType 或清旧权限掩盖问题。
