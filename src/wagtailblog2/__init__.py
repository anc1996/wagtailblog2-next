"""
WagtailBlog2 - 独立重建的现代化 Wagtail 内容管理与发布平台.

安全与装载边界：
1. 保持根包轻量纯粹，严禁在 __init__.py 中急切导入 Celery、数据库连接或 settings；
2. 严禁在此处执行猴子补丁或触发框架生命周期钩子；
3. 所有运行时模型、钩子与设置必须由 Django AppConfig 及 settings 显式注册与装载。
"""

__version__: str = "0.1.0"
