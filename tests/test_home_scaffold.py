"""P0-DEV-03 官方骨架回归：只装载和解析，不请求页面或访问存储。"""

from tools.e2_no_io_guard import install_no_io_guard

GUARD = install_no_io_guard()

from contextlib import contextmanager
from html.parser import HTMLParser
import importlib
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch


class _HTMLTags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class HomeScaffoldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(root / "src"))
        cls.addClassCleanup(sys.path.remove, str(root / "src"))
        os.environ["DJANGO_SETTINGS_MODULE"] = "wagtailblog2.settings.dev"

        import django

        before = GUARD.violations
        # 沿用 Home 合同的能力假设；不放行 SQLite 或网络探测。
        with patch(
            "modelsearch.backends.database.sqlite.utils.fts5_available",
            return_value=False,
        ), patch("socket.has_ipv6", False):
            django.setup()
        if GUARD.violations != before:
            raise AssertionError(f"Unexpected setup IO: {GUARD.events[before:]}")
        cls.setup_violations_after = GUARD.violations

    def tearDown(self):
        from django.db import connections

        self.assertTrue(GUARD.active)
        self.assertEqual(
            GUARD.violations,
            self.setup_violations_after,
            f"Unexpected scaffold IO: {GUARD.events[self.setup_violations_after:]}",
        )
        self.assertTrue(all(c.connection is None for c in connections.all()))

    @contextmanager
    def urls_for_debug(self, debug):
        from django.conf import settings
        from django.test import override_settings
        from django.urls import clear_url_caches

        urls = importlib.import_module(settings.ROOT_URLCONF)
        try:
            with override_settings(DEBUG=debug):
                importlib.reload(urls)
                clear_url_caches()
                yield urls
        finally:
            # override 已退出；恢复原模式下的路由及解析缓存。
            importlib.reload(urls)
            clear_url_caches()

    def test_default_home_template_renders_escaped_title_and_html_metadata(self):
        from django.template.loader import get_template
        from wagtailblog2.apps.home.models import HomePage

        self.assertEqual(HomePage.template, "site_home/home_page.html")
        template = get_template(HomePage.template)
        # 纯内存上下文，不实例化 Page，也不引入正式首页 UI 合同。
        title = '<em>首页 & "骨架"</em>'
        html = template.render({"page": SimpleNamespace(title=title)})
        self.assertIn(
            "&lt;em&gt;首页 &amp; &quot;骨架&quot;&lt;/em&gt;", html
        )
        self.assertNotIn(title, html)
        parsed = _HTMLTags()
        parsed.feed(html)
        self.assertTrue(
            any(tag == "html" and attrs.get("lang") == "zh-hans"
                for tag, attrs in parsed.tags),
            "Home HTML must declare lang=zh-hans",
        )
        viewport = [
            attrs.get("content", "")
            for tag, attrs in parsed.tags
            if tag == "meta" and attrs.get("name") == "viewport"
        ]
        self.assertTrue(
            any("width=device-width" in value.replace(" ", "")
                for value in viewport),
            "Home HTML must include a device-width viewport",
        )

    def test_django_filters_is_registered_and_native_widget_template_loads(self):
        from django.apps import apps
        from django.template.loader import get_template

        self.assertTrue(apps.is_installed("django_filters"))
        get_template("django_filters/widgets/multiwidget.html")

    def test_debug_routes_staticfiles_documents_and_page_catchall_last(self):
        from django.contrib.staticfiles.views import serve as staticfiles_serve
        from django.urls import resolve
        from wagtail import views as wagtail_views
        from wagtail.documents.views import serve as document_views

        with self.urls_for_debug(True) as urls:
            with self.subTest(route="staticfiles"):
                self.assertIs(
                    resolve("/static/wagtailadmin/css/core.css").func,
                    staticfiles_serve,
                )
            with self.subTest(route="documents"):
                self.assertIs(
                    resolve("/documents/1/scaffold.pdf").func, document_views.serve
                )
            with self.subTest(route="catchall-last"):
                match = urls.urlpatterns[-1].resolve("scaffold-page/")
                self.assertIsNotNone(match)
                self.assertIs(match.func, wagtail_views.serve)

    def test_media_has_no_direct_root_serve_in_either_debug_mode(self):
        from django.conf import settings
        from django.urls import Resolver404, URLResolver, resolve
        from django.views.static import serve as direct_serve
        from wagtail import views as wagtail_views
        from wagtail.documents.views import serve as document_views

        def patterns_in(patterns):
            for pattern in patterns:
                if isinstance(pattern, URLResolver):
                    yield from patterns_in(pattern.url_patterns)
                else:
                    yield pattern

        for debug in (True, False):
            with self.urls_for_debug(debug) as urls:
                for path in (
                    "/media/images/private.jpg",
                    "/media/documents/private.pdf",
                ):
                    with self.subTest(debug=debug, path=path):
                        try:
                            match = resolve(path)
                        except Resolver404:
                            pass
                        else:
                            self.assertIsNot(match.func, direct_serve)
                with self.subTest(debug=debug, contract="no-media-root-bypass"):
                    # 带点路径能穿过 Page 正则；同时检查注册树，防止潜伏的绕过入口。
                    for pattern in patterns_in(urls.urlpatterns):
                        self.assertFalse(
                            pattern.callback is direct_serve
                            and str(pattern.default_args.get("document_root"))
                            == str(settings.MEDIA_ROOT),
                            "Direct static.serve exposes MEDIA_ROOT outside "
                            "Wagtail resource permissions",
                        )
                if not debug:
                    with self.subTest(debug=debug, contract="native-routes"):
                        self.assertIs(
                            resolve("/static/scaffold/").func,
                            wagtail_views.serve,
                        )
                        try:
                            match = resolve("/static/wagtailadmin/css/core.css")
                        except Resolver404:
                            pass
                        else:
                            self.assertIs(match.func, wagtail_views.serve)
                        self.assertEqual(
                            resolve("/admin/login/").url_name, "wagtailadmin_login"
                        )
                        self.assertIs(
                            resolve("/documents/1/scaffold.pdf").func,
                            document_views.serve,
                        )


if __name__ == "__main__":
    unittest.main()
