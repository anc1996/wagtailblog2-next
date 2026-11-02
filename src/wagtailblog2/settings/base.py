"""
WagtailBlog2 基础共享配置 (base.py).

边界与架构原则 (ADR-P0-01 / ADR-P0-02 / ADR-P0-03 / ADR-P0-05 / ADR-P0-06)：
1. 装载 Django/Wagtail 核心、身份、公共资源及最小 HomePage，不装载 Blog/Guide；
2. 默认数据库采用本地独立 SQLite 路径 (var/db.sqlite3)，严禁连接旧站/生产 MySQL；
3. 默认缓存使用 LocMemCache，严禁连接共享 Redis；
4. 搜索后端使用 Wagtail 原生数据库搜索，严禁连接共享 Elasticsearch；
5. AUTH_USER_MODEL 已按 P0-DEV-01 固定；公共资源模型设置按 P0-DEV-02 激活；
6. 不在启动阶段导入 Celery，根包保持无副作用纯净性；
7. U40：当前不启用 Wagtail API v3，未来自定义业务 API 优先 DRF，本轮不开发接口。
"""

import os
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

# 基础路径解析：BASE_DIR 指向仓库根目录 (wagtailblog2-next)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# 优先加载根目录下的 .env 文件（若存在）
load_dotenv(BASE_DIR / ".env")

# 密钥配置：优先从环境变量读取，开发模式提供安全默认回退值
SECRET_KEY: str = os.getenv(
    "SECRET_KEY",
    "django-insecure-wagtailblog2-dev-placeholder-key-replace-in-production",
)

# 基础运行环境：base.py 默认关闭 DEBUG，各环境子配置按需覆盖
DEBUG: bool = False

# 主机访问允许列表
ALLOWED_HOSTS: List[str] = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]").split(",")
    if host.strip()
]

# =============================================================================
# 应用安装清单 (INSTALLED_APPS)
# =============================================================================
INSTALLED_APPS: List[str] = [
    # 本项目根应用（支持 static / templates 目录自动发现）
    "wagtailblog2.apps.core.Wagtailblog2Config",
    # 稳定身份 App label 与 User 模型合同见 ADR-P0-02/03/05。
    "wagtailblog2.apps.identity.apps.IdentityConfig",
    # 公共资源持久身份独立于 Blog/Guide，注册不执行外部 IO。
    "wagtailblog2.apps.resources.apps.ResourcesConfig",
    # 首页 Page 仅使用 Wagtail 原生生命周期，不初始化 Site/Locale 数据。
    "wagtailblog2.apps.home.apps.HomeConfig",

    # Wagtail 核心与功能组件 (ADR-P0-06)
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.embeds",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail",

    # 支撑与第三方库
    "modelcluster",
    "taggit",
    # 官方骨架注册此 App，以便原生筛选器发现自己的 widget 模板。
    "django_filters",
    "rest_framework",

    # Django 核心基础应用
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

# =============================================================================
# 认证与持久模型身份契约 (ADR-P0-03 / ADR-P0-05)
#
# 1. P0-DEV-01 已批准并装载最小 AbstractUser；它仍未生成迁移或连接数据库。
# 2. P0-DEV-02 仅激活公共资源最小模型；迁移与真实媒体 IO 仍需另行授权。
# 3. 身份 App 的持久 label 与 AUTH_USER_MODEL 不得在首次迁移后随意改名。
# =============================================================================
# 持久身份合同：首版使用最小 AbstractUser，不附带会员或业务资料字段。
AUTH_USER_MODEL: str = "site_identity.User"
WAGTAILIMAGES_IMAGE_MODEL: str = "resources.Image"
WAGTAILDOCS_DOCUMENT_MODEL: str = "resources.Document"

# =============================================================================
# 中间件配置 (MIDDLEWARE)
# =============================================================================
MIDDLEWARE: List[str] = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
]

ROOT_URLCONF: str = "wagtailblog2.urls"

# =============================================================================
# 模板引擎配置 (TEMPLATES)
# =============================================================================
TEMPLATES: List[Dict[str, Any]] = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "src" / "wagtailblog2" / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION: str = "wagtailblog2.wsgi.application"
ASGI_APPLICATION: str = "wagtailblog2.asgi.application"

# =============================================================================
# 数据库配置 (DATABASES)
#
# 隔离与红线原则 (ADR-P0-01 / ADR-P0-06)：
# 1. 骨架阶段默认使用本地独立 SQLite 文件路径，严禁指向旧站/生产 MySQL；
# 2. 未经用户明确书面授权，不得执行 migrate 或实际创建生产/旧库表结构。
# =============================================================================
DATABASES: Dict[str, Dict[str, Any]] = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "var" / "db.sqlite3",
    }
}

# =============================================================================
# 密码校验规则 (AUTH_PASSWORD_VALIDATORS)
# =============================================================================
AUTH_PASSWORD_VALIDATORS: List[Dict[str, str]] = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# =============================================================================
# 国际化与时区配置
# =============================================================================
LANGUAGE_CODE: str = "zh-hans"
TIME_ZONE: str = "Asia/Shanghai"
USE_I18N: bool = True
USE_TZ: bool = True

# =============================================================================
# 静态文件与媒体文件配置 (Static & Media)
# =============================================================================
STATICFILES_FINDERS: List[str] = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

STATICFILES_DIRS: List[Path] = [
    BASE_DIR / "src" / "wagtailblog2" / "static",
]

STATIC_ROOT: Path = BASE_DIR / "var" / "static"
STATIC_URL: str = "/static/"

MEDIA_ROOT: Path = BASE_DIR / "var" / "media"
MEDIA_URL: str = "/media/"

# =============================================================================
# Wagtail 平台核心配置
# =============================================================================
WAGTAIL_SITE_NAME: str = os.getenv("WAGTAIL_SITE_NAME", "WagtailBlog2")
WAGTAILADMIN_BASE_URL: str = os.getenv("WAGTAILADMIN_BASE_URL", "http://localhost:8000")

# 搜索后端：使用 Wagtail 原生数据库搜索，严禁在骨架阶段连接外部 Elasticsearch
WAGTAILSEARCH_BACKENDS: Dict[str, Dict[str, str]] = {
    "default": {
        "BACKEND": "wagtail.search.backends.database",
    }
}

DEFAULT_AUTO_FIELD: str = "django.db.models.BigAutoField"

# =============================================================================
# 缓存配置 (CACHES)
#
# 骨架阶段默认使用本地内存缓存，严禁连接共享 Redis
# =============================================================================
CACHES: Dict[str, Dict[str, str]] = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "wagtailblog2-local-cache",
    }
}
