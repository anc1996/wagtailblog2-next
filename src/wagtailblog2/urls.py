"""
WagtailBlog2 核心 URL 路由配置.

边界与生命周期原则 (ADR-P0-06)：
1. Wagtail 原生路由体系是页面树生命周期与发布的权威入口；
2. Django 原生管理后台挂载于 /django-admin/，Wagtail 管理后台挂载于 /admin/；
3. 文档服务挂载于 /documents/；
4. 页面树统配路由挂载于根路径，由 Wagtail 核心视图统一调度；
5. 不导入旧站业务视图、旧版 API 或旧搜索路由。
"""

from typing import List, Union

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

urlpatterns: List[Union[URLPattern, URLResolver]] = [
    path("django-admin/", admin.site.urls),
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    # 未来可在此注册获批的 API 路由，如 path("api/v2/", api_router.urls)
    # Wagtail 页面树统配路由必须放在最后，兜底所有 Page URL
    path("", include(wagtail_urls)),
]

if settings.DEBUG:
    # 开发模式下通过 Django 静态文件辅助函数托管本地 media，生产环境严禁由此托管
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
