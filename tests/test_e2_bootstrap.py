"""Guarded project loading only: no media or migration acceptance."""

from tools.e2_no_io_guard import install_no_io_guard

GUARD = install_no_io_guard()

import importlib
import io
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


class SkeletonBootstrapTests(unittest.TestCase):
    def test_skeleton_loads_with_explicit_mock_of_sqlite_fts5_capability(self):
        root = Path(__file__).resolve().parents[1]
        self.assertTrue(GUARD.active)
        self.assertNotIn("wagtailblog2.settings.dev", sys.modules)
        before = GUARD.violations
        sys.path.insert(0, str(root / "src"))
        os.environ["DJANGO_SETTINGS_MODULE"] = "wagtailblog2.settings.dev"
        try:
            import django

            # modelsearch 1.3.2 probes sqlite3.connect(":memory:") at import.
            # Do not whitelist DB IO or pretend that FTS5 was verified. Only
            # this test assumes FTS5 unavailable; the raw guarded check fails.
            with patch(
                "modelsearch.backends.database.sqlite.utils.fts5_available",
                return_value=False,
            ) as fts5_probe, patch("socket.has_ipv6", False):
                # urllib3 otherwise opens/binds a socket for an import-time IPv6
                # capability probe, catches the violation, and keeps importing.
                # This is another explicit capability Mock, not network evidence.
                django.setup()
            fts5_probe.assert_called_once_with()
            from django.apps import apps
            from django.conf import settings
            from django.core.management import call_command
            from django.db import connections
            from django.urls import resolve

            configured = importlib.import_module(settings.SETTINGS_MODULE)
            self.assertEqual(
                Path(configured.__file__).resolve(),
                root / "src/wagtailblog2/settings/dev.py",
            )
            self.assertEqual(resolve("/django-admin/login/").view_name, "admin:login")
            self.assertEqual(resolve("/admin/login/").url_name, "wagtailadmin_login")
            self.assertTrue(importlib.import_module("wagtailblog2.urls").urlpatterns)
            self.assertTrue(
                callable(importlib.import_module("wagtailblog2.wsgi").application)
            )
            self.assertTrue(
                callable(importlib.import_module("wagtailblog2.asgi").application)
            )
            # The system check calls the same probe again. Keep this explicit
            # Mock scoped to that call and retain its expected fallback warning.
            stderr = io.StringIO()
            with patch(
                "modelsearch.backends.database.sqlite.utils.fts5_available",
                return_value=False,
            ), patch.object(
                # Django 6.1 checks JSONField support by opening a cursor.
                # This skeleton test must mock the capability instead of
                # weakening the process-wide database tripwire.
                type(connections["default"].features),
                "supports_json_field",
                True,
            ):
                # 先运行默认系统检查；Django 6.1 默认不执行 compatibility
                # 标签，再单独验证 fallback 警告。两次都保持同一 IO 守卫。
                call_command("check", verbosity=0, stderr=stderr)
                call_command(
                    "check",
                    verbosity=0,
                    stderr=stderr,
                    tags=["compatibility"],
                )
            self.assertIn("modelsearch.W003", stderr.getvalue())

            # P0-DEV-01 fixed identity; P0-DEV-02 resources and P0-DEV-03
            # HomePage now load their model identities. Migrations remain
            # intentionally outside this slice and are not inferred from
            # successful model loading.
            self.assertEqual(settings.AUTH_USER_MODEL, "site_identity.User")
            self.assertEqual(settings.WAGTAILIMAGES_IMAGE_MODEL, "resources.Image")
            self.assertEqual(settings.WAGTAILDOCS_DOCUMENT_MODEL, "resources.Document")
            project_apps = [
                app for app in apps.get_app_configs()
                if app.name == "wagtailblog2" or app.name.startswith("wagtailblog2.")
            ]
            self.assertEqual(
                [app.name for app in project_apps],
                [
                    "wagtailblog2",
                    "wagtailblog2.apps.identity",
                    "wagtailblog2.apps.resources",
                    "wagtailblog2.apps.home",
                ],
            )
            self.assertEqual(list(project_apps[0].get_models()), [])
            self.assertEqual(
                [model._meta.label for model in project_apps[1].get_models()],
                ["site_identity.User"],
            )
            self.assertEqual(
                [model._meta.label for model in project_apps[2].get_models()],
                ["resources.Image", "resources.Rendition", "resources.Document"],
            )
            self.assertEqual(
                [model._meta.label for model in project_apps[3].get_models()],
                ["site_home.HomePage"],
            )
            self.assertEqual(list((root / "src/wagtailblog2").rglob("migrations")), [])
            self.assertTrue(all(c.connection is None for c in connections.all()))
            self.assertEqual(
                GUARD.violations, before,
                f"Unexpected bootstrap IO entries: {GUARD.events[before:]}",
            )
        finally:
            sys.path.remove(str(root / "src"))


if __name__ == "__main__":
    unittest.main()
