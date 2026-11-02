# ADR-P0-07：新站迁移依赖图与分层验证门禁

- 日期：2026-10-31
- 状态：迁移 B 已由 U38 确认；节点/边仍为候选，不是已生成或已验证 DAG。
- 证据级别：E1；未生成迁移，未运行 loader 或真实迁移。
- 用户批准：迁移 B、resources/site_home 基础身份已确认；节点/边、模型状态和真实迁移仍未验证。

## 来源与用户已确认

依据旧参考仓库 `说明书/00-产品需求与项目管理/` 的 00、02 P0、04 U17/U24/U26、08、09 §10.1～10.2、10 §12～14。已确认独立仓库和最小 AbstractUser；旧库/迁移链不约束新模型，亦不得因此被删除。首次建库/迁移与真实服务操作需要具体授权。

U27～U36、U38 产品确认已固定迁移路线 B 和基础 App 身份，但不替代迁移图实证；本轮已批准 `site_identity.User` 的 P0-DEV-01 实现。依赖边和真实迁移仍待验证，技术批准与 E2/E3 证明是不同门禁。

## 方案建议与备选

采用**迁移 B（U38）**：新仓库独立 settings、App 所有权与必要自有 label；保留第三方迁移，不装旧业务。测试与未来正式共用产品模型历史，fixtures 为仅测试附加图。

**迁移 A**（同 label/新迁移模块）仅保留为技术备忘，不作为当前实施路线；`MIGRATION_MODULES` 不隔离 models/ready/hooks，不能通过映射或 None 隐藏业务依赖。已获批的仓库选项 A 与迁移 B 均已分别记录，不混同。

## 历史源码依赖摘录，不是当前完整图

下表转述旧 09 §10.2/10 §12 对安装源码的审计，本批未重检安装环境；省略各 App 的内部前序，不可直接当执行计划。

| 历史节点 | 摘录的关键依赖/用途 |
|---|---|
| contenttypes.0001 / auth.0001 | contenttypes 初始无外部依赖；auth 初始引用 contenttypes 首节点 |
| admin.0001 | User swappable 与 contenttypes 首节点 |
| wagtailcore 初始 squash | User、Page swappable、auth/contenttypes 首节点；默认 Page 的同 App 解析需 loader 处理，不能仅凭文本判为环 |
| wagtailcore.0024 / .0025 / .0026 / .0028 | Collection 结构、根 Collection 数据、Collection 权限、合并节点 |
| wagtailadmin.0001 / wagtailusers.0001 | 分别涉及 core.0026 / User |
| wagtailimages 初始 squash / .0023 | 初始含 User、taggit.0001、core.0002/.0026；.0023 引用 wagtailadmin.0001 |
| wagtaildocs.0001 / .0005 / .0006 / .0011 | User/taggit，后续含 core.0025、core.0026、wagtailadmin.0001 |
| wagtailmedia.0001 | taggit.0002、core.0028、User；留 P2a 评估 |

历史最高文件名不等于 loader 的实际叶节点，squash/replaces、swappable 与模型状态必须整体解析。抽象资源继承不建立到原生具体资源表的多表父链接，也不证明全部原生资源迁移/表可移除。

## 自有图候选与所有权

| 自有节点候选 | 输入依赖/预期状态 | 禁止反向边或冲突 |
|---|---|---|
| `site_identity.0001_initial` | 创建最小 User；groups/user_permissions 所需 auth 边由实际生成状态审阅，不机械固定 auth.0012 | 不依赖 resources、home、Page、people |
| `resources.0001_initial` | `swappable_dependency(AUTH_USER_MODEL)`、`taggit.0001_initial`、`wagtailcore.0025_collection_initial_data` 是候选；建立 Collection/上传者/标签、Rendition→Image 及原生约束 | 不依赖 Blog/Guide/fixtures；实际缺失前序不得略过 |
| `site_home.0001_initial` | 原生 Page 多表继承，实际生成后审核完整 core 图前序 | 不照抄旧 Home 的 run_before core.0053 再叠加其后继依赖 |
| `resource_fixtures.0001_initial` | Page + 公共 Image；测试附加图 | 任何生产节点不得依赖 fixtures |
| 后续业务/插件迁移 | 由所属 App 追加，跨 App 边显式 | 不以功能开关改变已采用历史，不改写已应用迁移 |

概念顺序如下，箭头表示“先决条件 → 消费者”，不是完整节点图：

```text
contenttypes → auth 必要关系状态 → site_identity.User 初始迁移
site_identity.User + auth/contenttypes + 原生依赖解析 → Wagtail 原生图
User 初始 + taggit + core Collection 前序 → resources 初始
核验后的 core Page 前序 → site_home 初始
核验后的 core Page 前序 + resources.Image → resource_fixtures（仅测试）
```

关键无环条件是 User 初始无资源/Page 回边；后续头像/人员等关联另迁移设计。`swappable_dependency` 解析目标 App 首节点，不能替代全图与状态验证。图需同时含必要第三方内部边，不能只让上述四个自有节点看似无环。

## 待用户批准决定与未验证项

- 验证迁移 B 下自有 App 的初始节点与模型结构；`site_identity`、`resources`、`site_home` 身份已确认，测试夹具身份仍按实施需要确定；依赖 [ADR-P0-03](ADR-P0-03.md)、[ADR-P0-04](ADR-P0-04.md)、[ADR-P0-05](ADR-P0-05.md)。
- 后续配置/原型实施授权与 E3 具体主机/空库等授权分别取得，不由文档审定推导。
- 未验证：真实节点/边/叶、squash 替换、循环、模型状态、反向关系、生成差异、后端 SQL/第三方数据迁移、真实权限与 chooser。

## 风险与依赖

依赖 [ADR-P0-06](ADR-P0-06.md) 的固定配置与导入守卫。风险为 User 不在首迁移、旧 Home run_before 冲突、忽略 Collection 数据迁移、误删框架图、夹具污染生产、非空目标被当新库。无环只是一项必要条件，不足以证明数据库可初始化。

## 验证计划、停止与回退

1. **E1，本批范围：**审阅候选图、边来源、所有权、命名、禁用操作与验证计划；不生成迁移、不导入 settings。
2. **E2，获批配置/原型范围内：**在项目导入前阻断 DB（含本地 SQLite）、网络、Storage、任务和子进程，先证明守卫有效，再受守卫装载，受控评估 `MigrationLoader(None)` 等只读入口；仅核对已有 AppConfig/模型/迁移源码及内存中的节点/边/叶/replaces、状态、环和关系。缺少自有迁移时记录缺项，不生成迁移补齐证据；不运行 migrate、makemigrations、collectstatic、runserver，不连真实服务、不开展 E3。不能用移除必要 App、fake 或换迁移历史“修复”。
3. **E3，另获具体目标操作授权：**预检目标表/数据/迁移历史；确认为获准空库后执行实际迁移，核对第三方数据、ContentType/权限、User/资源/Collection/后台。E2 不能证明 SQL 和数据迁移正确，E3 也不推定生产升级安全。
4. **停止：**缺节点、环、状态漂移、旧业务装载、任何越界 IO、目标非空/历史不明；保留证据并退回设计，不清库/fake/覆盖旧链。
5. **回退检查：**文档/未落库原型可按文件归属撤回；发生 SQL 提交后先核实状态。反向迁移/删库/恢复均非本 ADR 自动授权，不使用 destructive reset 或删除 Mongo 版本补偿。

验收记录必须分别列 E1/E2/E3 的命令、环境、范围、结果和未测项；E3 正确性未证明前，不标记“P0 建库设计实证通过”，不自动进入 P1。

## P0-DEV-02 实施记录（2026-11-02）

- 已完成 `resources` App 与三类资源模型的代码装载、关系/约束合同测试和导入前无外部 IO 验证。
- 当前仅审查候选依赖方向：`site_identity.User`、taggit、Wagtail Collection 前序 → `resources` 初始模型；这不是已生成的迁移 DAG。
- 本切片未创建迁移文件、未运行 MigrationLoader、`makemigrations` 或 `migrate`；第三方 squash/replaces、叶节点、真实状态和首次数据库迁移仍待后续 E2/E3 门禁。
- 本节覆盖此前“resources App 尚未实现”的当前状态，不覆盖完整迁移图验收。

## P0-DEV-03 实施记录（2026-11-02）

- `HomePage` 采用 Wagtail 原生 `Page` 多表继承；候选 `site_home.0001_initial` 仍须依赖实际核验的原生 Page 迁移前序。
- 本切片未生成迁移文件、未运行 MigrationLoader 或迁移；自有与第三方完整迁移 DAG 仍未验证。
- Home 测试在 `django.setup()` 的 Wagtail API schema 构造阶段被 `Discriminator must be used with a Union type` 阻断；因此本轮没有模型注册或迁移图的运行时证据。

### 恢复验证增量（2026-11-02）

- 后续隔离 8.1rc1 测试已证明 Home 模型注册、原生 Page 多表父链接及模型检查；它覆盖上面的“没有模型注册运行证据”，不覆盖正式 8.0.1 的启动阻断或完整迁移 DAG 未验证事实。
- 候选关系仍为核验后的 `wagtailcore.Page` 迁移前序 → `site_home.0001_initial`；User 初始不得反依赖 Home/Resources。实际依赖节点、squash/replaces、叶节点及状态须在获批迁移图工作中验证，不照抄旧站 `run_before`。
- U40 API 技术策略不引入新模型、迁移节点或第二套发布/权限权威；本轮没有生成迁移、运行 MigrationLoader、迁移或连接服务。正式版本升级仍需独立批准。
