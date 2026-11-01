# WagtailBlog2 Codex 治理配置

## 文件

- `config.toml`：仓库级角色声明和默认架构师路由。
- `agents/terra.toml`：Terra 主代理声明。
- `agents/sol.toml`：Sol 首席架构师声明。
- `agents/gemini.toml`：Gemini 工程实现声明。
- `AGENTS_INTERACTION_PROTOCOL.md`：实际派单、证据分级和权限边界。
- `skills/wagtailblog-dev-workflow/SKILL.md`：本仓库的开发与验证门禁。

## 证据边界

本配置通过 TOML 解析和静态一致性检查后，只能证明文件结构和声明互相一致。模型名、provider、推理等级、nickname、配置目录或技能文件不证明运行时底层模型、供应商、权限隔离、网络边界或工具可用性。

本轮已使用 Codex 原生子代理机制实际派发 Sol、Gemini 和独立审查代理；具体运行状态与复核结果以主会话工具返回为准。后续报告必须把这一事实与静态配置结果分开记录。

## 最小核查

在仓库根目录执行：

```powershell
python tools/check_codex_agents.py
```

该命令仅解析本地 TOML、检查角色文件和拒绝旧仓库路径，不启动代理、不访问 MCP、不连接外部服务。
