"""P0-DEV-03 HomePage 合同的无外部 IO 验证。"""

import importlib
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from tools.e2_no_io_guard import install_no_io_guard


GUARD = install_no_io_guard()


class HomeContractTests(unittest.TestCase):
    """只验证 Home 身份和原生 Page 边界，不创建 Site/Locale 或数据库记录。"""

    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.root = root
        sys.path.insert(0, str(root / "src"))
        os.environ["DJANGO_SETTINGS_MODULE"] = "wagtailblog2.settings.dev"

        import django

        before = GUARD.violations
        with patch(
            "modelsearch.backends.database.sqlite.utils.fts5_available",
            return_value=False,
        ), patch("socket.has_ipv6", False):
            django.setup()
        cls.setup_violations_before = before
        cls.setup_violations_after = GUARD.violations
        if cls.setup_violations_after != before:
            raise AssertionError(
                f"Unexpected Home setup IO entries: {GUARD.events[before:]}"
            )

        cls.apps = importlib.import_module("django.apps").apps
        cls.settings = importlib.import_module("django.conf").settings
        cls.HomePage = importlib.import_module(
            "wagtailblog2.apps.home.models"
        ).HomePage

    @classmethod
    def tearDownClass(cls):
        sys.path.remove(str(cls.root / "src"))

    def test_home_app_uses_approved_persistent_identity(self):
        config = self.apps.get_app_config("site_home")
        self.assertEqual(config.name, "wagtailblog2.apps.home")
        self.assertEqual(config.label, "site_home")

    def test_home_page_is_registered_with_wagtail_page_identity(self):
        from wagtail.models import Page

        self.assertTrue(issubclass(self.HomePage, Page))
        self.assertEqual(self.HomePage._meta.label, "site_home.HomePage")
        self.assertIs(self.apps.get_model("site_home", "HomePage"), self.HomePage)
        page_link = self.HomePage._meta.get_field("page_ptr")
        self.assertIs(self.HomePage._meta.parents[Page], page_link)
        self.assertIs(page_link.remote_field.model, Page)
        self.assertTrue(page_link.remote_field.parent_link)
        self.assertTrue(page_link.one_to_one)
        self.assertTrue(page_link.primary_key)

    def test_home_page_keeps_native_parent_and_subpage_extensibility(self):
        from wagtail.models import Page

        self.assertIsNone(getattr(self.HomePage, "parent_page_types", None))
        self.assertIsNone(getattr(self.HomePage, "subpage_types", None))
        # 当前仅注册 Page/HomePage；验证原生双向解析结果，不能只检查缺省声明。
        # allowed_* 包含不可创建的原生 Page，且只读取类注册表，无需实例或数据库。
        self.assertCountEqual(
            self.HomePage.allowed_parent_page_models(), [Page, self.HomePage]
        )
        self.assertCountEqual(
            self.HomePage.allowed_subpage_models(), [Page, self.HomePage]
        )

    def test_home_page_keeps_native_lifecycle_and_model_checks(self):
        from wagtail.models import Page

        self.assertIs(self.HomePage.base_page_model, Page)
        self.assertEqual(self.HomePage.check(), [])
        # 比较实际继承的方法，不调用会写库的生命周期入口。
        for method in ("save", "save_revision", "publish", "unpublish", "delete"):
            with self.subTest(method=method):
                self.assertIs(getattr(self.HomePage, method), getattr(Page, method))

    def test_identity_and_resources_contracts_remain_configured(self):
        from django.urls import resolve
        from wagtail import views as wagtail_views
        from wagtail.documents.views import serve as document_views
        from wagtail.models import Locale

        self.assertEqual(self.settings.AUTH_USER_MODEL, "site_identity.User")
        self.assertEqual(
            self.settings.WAGTAILIMAGES_IMAGE_MODEL, "resources.Image"
        )
        self.assertEqual(
            self.settings.WAGTAILDOCS_DOCUMENT_MODEL, "resources.Document"
        )
        self.assertTrue(self.apps.is_installed("wagtail.contrib.redirects"))
        self.assertIn(
            "wagtail.contrib.redirects.middleware.RedirectMiddleware",
            self.settings.MIDDLEWARE,
        )
        self.assertTrue(self.apps.is_installed("wagtail.documents"))
        # 只解析路由与字段元数据，保留文档交付和原生 Locale，不执行请求或查询。
        self.assertIs(
            resolve("/documents/1/contract.pdf").func, document_views.serve
        )
        self.assertIs(
            self.HomePage._meta.get_field("locale").remote_field.model, Locale
        )
        self.assertFalse(self.apps.is_installed("wagtail.api.v3"))
        self.assertIs(resolve("/api/v3/").func, wagtail_views.serve)

    def test_home_setup_did_not_open_database_or_run_migrations(self):
        from django.db import connections

        self.assertTrue(GUARD.active)
        self.assertTrue(all(connection.connection is None for connection in connections.all()))
        self.assertEqual(
            GUARD.violations,
            self.setup_violations_after,
            f"Unexpected Home setup IO entries: {GUARD.events[self.setup_violations_before:]}",
        )
        self.assertEqual(
            list((self.root / "src/wagtailblog2").rglob("migrations")), []
        )


if __name__ == "__main__":
    unittest.main()
