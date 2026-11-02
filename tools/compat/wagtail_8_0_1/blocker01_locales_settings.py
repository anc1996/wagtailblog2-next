"""仅供隔离进程启用 Locales；须先装无 IO 守卫，不改项目设置或初始化数据。"""
from wagtailblog2.settings.dev import *
INSTALLED_APPS = [*INSTALLED_APPS, "wagtail.locales"]
