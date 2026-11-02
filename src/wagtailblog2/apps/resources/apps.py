"""公共资源的稳定应用身份。"""

from django.apps import AppConfig


class ResourcesConfig(AppConfig):
    """仅注册模型，不在启动阶段连接数据库或外部服务。"""

    # label 是迁移、ContentType 和权限的持久身份，不随 Python 包重构漂移。
    name: str = "wagtailblog2.apps.resources"
    label: str = "resources"
    verbose_name: str = "WagtailBlog2 公共资源"
    default_auto_field: str = "django.db.models.BigAutoField"
