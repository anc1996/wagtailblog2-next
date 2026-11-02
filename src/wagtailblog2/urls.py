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
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import URLPattern, URLResolver, include, path
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

urlpatterns: List[Union[URLPattern, URLResolver]] = [
    path("django-admin/", admin.site.urls),
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    # U40：未来自定义业务 API 优先 DRF；本轮不注册业务 API 或 Wagtail API v3。
]

if settings.DEBUG:
    # 与官方骨架一致，仅在开发模式提供应用静态文件（包含后台 CSS/JS）。
    # 不直出整个 MEDIA_ROOT：草稿/私有原件不能绕过资源权限；图片交付留到 P1。
    urlpatterns += staticfiles_urlpatterns()

# 页面入口始终置于最后；文档继续经过 Wagtail 原生交付逻辑。
urlpatterns += [path("", include(wagtail_urls))]
