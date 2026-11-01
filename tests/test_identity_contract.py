"""P0-DEV-01 身份合同的无外部 IO 验证。"""

import importlib
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from tools.e2_no_io_guard import install_no_io_guard


GUARD = install_no_io_guard()


class IdentityContractTests(unittest.TestCase):
    """验证最小 User、App label 和 settings 合同。"""

    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.root = root
        sys.path.insert(0, str(root / "src"))
        os.environ["DJANGO_SETTINGS_MODULE"] = "wagtailblog2.settings.dev"

        import django

        # Wagtail 当前依赖链可能探测 SQLite FTS5/IPv6；这里只使用显式
        # Mock，避免把能力假设误报成真实数据库或网络证据。
        setup_violations_before = GUARD.violations
        with patch(
            "modelsearch.backends.database.sqlite.utils.fts5_available",
            return_value=False,
        ), patch("socket.has_ipv6", False):
            django.setup()

        cls.apps = importlib.import_module("django.apps").apps
        cls.settings = importlib.import_module("django.conf").settings
        # Setup must not add guarded IO events; prior negative probes, if any,
        # are allowed and are excluded from this boundary comparison.
        cls.setup_violations_before = setup_violations_before
        cls.setup_violations_after = GUARD.violations
        if cls.setup_violations_after != cls.setup_violations_before:
            raise AssertionError(
                "Unexpected identity setup IO entries: "
                f"{GUARD.events[cls.setup_violations_before:]}"
            )

    @classmethod
    def tearDownClass(cls):
        sys.path.remove(str(cls.root / "src"))

    def test_identity_app_uses_persistent_label_and_user_model(self):
        app_config = self.apps.get_app_config("site_identity")

        self.assertEqual(app_config.name, "wagtailblog2.apps.identity")
        self.assertEqual(self.settings.AUTH_USER_MODEL, "site_identity.User")

    def test_identity_user_is_minimal_abstract_user_extension(self):
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import AbstractUser

        user_model = get_user_model()

        self.assertTrue(issubclass(user_model, AbstractUser))
        self.assertEqual(user_model._meta.app_label, "site_identity")
        self.assertEqual(user_model.__name__, "User")
        self.assertEqual(user_model.__module__, "wagtailblog2.apps.identity.models")

    def test_identity_app_does_not_connect_to_database_during_setup(self):
        self.assertTrue(GUARD.active)
        self.assertIsNone(importlib.import_module("django.db").connection.connection)
        self.assertEqual(
            GUARD.violations,
            self.setup_violations_after,
            f"Unexpected identity setup IO entries: "
            f"{GUARD.events[self.setup_violations_before:]}",
        )


if __name__ == "__main__":
    unittest.main()
