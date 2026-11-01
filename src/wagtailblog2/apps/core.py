"""WagtailBlog2 根应用配置。

根应用只负责项目级静态资源和模板发现，不注册业务模型或外部服务。
"""

from django.apps import AppConfig


class Wagtailblog2Config(AppConfig):
    """WagtailBlog2 根包的无副作用 AppConfig。"""

    name: str = "wagtailblog2"
    verbose_name: str = "WagtailBlog2 核心平台"
    default_auto_field: str = "django.db.models.BigAutoField"

    def ready(self) -> None:
        """启动阶段保持零外部 IO。"""

        return None
