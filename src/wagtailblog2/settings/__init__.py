"""
WagtailBlog2 设置模块包.

架构原则 (ADR-P0-02 / ADR-P0-06)：
- base.py: 核心共享配置（App 列表、中间件、模板、安全占位等）；
- dev.py: 本地开发配置（继承 base.py，DEBUG=True，独立 SQLite 路径）；
- 严禁在此模块内隐式导入外部配置或直接连接旧站服务。
"""
