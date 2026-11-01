"""新站身份 AppConfig。

该 App 只承载最小登录身份，不承载会员、人员展示资料或业务字段。
"""

from django.apps import AppConfig


class IdentityConfig(AppConfig):
    """注册持久身份模型及其稳定 Django app label。"""

    # AppConfig.name 是 Python 导入路径；label 是迁移、ContentType 和权限的持久身份。
    name: str = "wagtailblog2.apps.identity"
    label: str = "site_identity"
    verbose_name: str = "WagtailBlog2 身份"
    default_auto_field: str = "django.db.models.BigAutoField"

    def ready(self) -> None:
        """保持启动阶段无副作用，不连接数据库或外部服务。"""

        return None
