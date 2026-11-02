"""首页 AppConfig，固定 Home 的 Django 持久身份。"""

from django.apps import AppConfig


class HomeConfig(AppConfig):
    """仅注册首页 Page，不在启动阶段创建 Site/Locale 或执行外部 IO。"""

    name: str = "wagtailblog2.apps.home"
    label: str = "site_home"
    verbose_name: str = "WagtailBlog2 首页"
    default_auto_field: str = "django.db.models.BigAutoField"
