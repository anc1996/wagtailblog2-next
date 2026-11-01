"""
WagtailBlog2 本地开发环境设置 (dev.py).

边界与隔离要求 (ADR-P0-06)：
1. 继承 base.py 核心配置；
2. 开启 DEBUG=True，仅用于本地开发与测试调试；
3. 允许本地回环地址访问；
4. 邮件后端采用控制台输出，防止外发网络请求；
5. 保持零 IO 守卫，严禁在此隐式连接旧站服务。
"""

import os
from typing import List

from .base import *  # noqa: F401, F403

DEBUG: bool = True

SECRET_KEY: str = os.getenv(
    "SECRET_KEY",
    "django-insecure-wagtailblog2-dev-placeholder-key-replace-in-production",
)

# 允许本地开发访问
ALLOWED_HOSTS: List[str] = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]").split(",")
    if host.strip()
]

# 本地控制台邮件后端（避免网络 IO）
EMAIL_BACKEND: str = "django.core.mail.backends.console.EmailBackend"
