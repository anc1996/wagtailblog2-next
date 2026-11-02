"""P0-DEV-02 公共资源模型合同的无外部 IO 验证。"""

import importlib
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from tools.e2_no_io_guard import install_no_io_guard


GUARD = install_no_io_guard()


class ResourcesContractTests(unittest.TestCase):
    """只验证模型身份、原生关系和设置，不执行数据库或文件存储操作。"""

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
                "Unexpected resource setup IO entries: "
                f"{GUARD.events[before:]}"
            )

        cls.apps = importlib.import_module("django.apps").apps
        cls.settings = importlib.import_module("django.conf").settings
        cls.Image = importlib.import_module(
            "wagtailblog2.apps.resources.models"
        ).Image
        cls.Rendition = importlib.import_module(
            "wagtailblog2.apps.resources.models"
        ).Rendition
        cls.Document = importlib.import_module(
            "wagtailblog2.apps.resources.models"
        ).Document

    @classmethod
    def tearDownClass(cls):
        sys.path.remove(str(cls.root / "src"))

    def test_resources_app_uses_approved_persistent_identity(self):
        config = self.apps.get_app_config("resources")
        self.assertEqual(config.name, "wagtailblog2.apps.resources")
        self.assertEqual(config.label, "resources")

    def test_models_use_approved_wagtail_identities(self):
        from wagtail.documents.models import AbstractDocument
        from wagtail.images.models import AbstractImage, AbstractRendition

        self.assertTrue(issubclass(self.Image, AbstractImage))
        self.assertTrue(issubclass(self.Rendition, AbstractRendition))
        self.assertTrue(issubclass(self.Document, AbstractDocument))
        self.assertEqual(self.Image._meta.label, "resources.Image")
        self.assertEqual(self.Rendition._meta.label, "resources.Rendition")
        self.assertEqual(self.Document._meta.label, "resources.Document")
        self.assertEqual(
            self.Image.__module__, "wagtailblog2.apps.resources.models"
        )
        self.assertEqual(
            self.Rendition.__module__, "wagtailblog2.apps.resources.models"
        )
        self.assertEqual(
            self.Document.__module__, "wagtailblog2.apps.resources.models"
        )

    def test_wagtail_settings_resolve_to_resources_models(self):
        from wagtail.documents import get_document_model
        from wagtail.images import get_image_model

        self.assertEqual(
            self.settings.WAGTAILIMAGES_IMAGE_MODEL, "resources.Image"
        )
        self.assertEqual(
            self.settings.WAGTAILDOCS_DOCUMENT_MODEL, "resources.Document"
        )
        self.assertIs(get_image_model(), self.Image)
        self.assertIs(get_document_model(), self.Document)
        self.assertIs(get_image_model().get_rendition_model(), self.Rendition)

    def test_image_and_document_keep_native_collection_user_and_tags(self):
        from django.contrib.auth import get_user_model

        user = get_user_model()
        for model in (self.Image, self.Document):
            self.assertEqual(
                model._meta.get_field("collection").remote_field.model._meta.label,
                "wagtailcore.Collection",
            )
            self.assertEqual(
                model._meta.get_field("uploaded_by_user").remote_field.model,
                user,
            )
            self.assertIn("tags", {field.name for field in model._meta.get_fields()})

    def test_resource_models_have_no_native_reverse_relation_clashes(self):
        # 与原生同名模型共存时，上传者/标签反向关系仍必须通过模型检查。
        for model in (self.Image, self.Rendition, self.Document):
            with self.subTest(model=model._meta.label):
                self.assertEqual(model.check(), [])

    def test_rendition_points_to_custom_image_and_keeps_native_uniqueness(self):
        from django.db import models

        image_field = self.Rendition._meta.get_field("image")
        self.assertIs(image_field.remote_field.model, self.Image)
        self.assertEqual(image_field.remote_field.related_name, "renditions")
        self.assertIs(image_field.remote_field.on_delete, models.CASCADE)

        unique_constraints = [
            constraint
            for constraint in self.Rendition._meta.constraints
            if constraint.__class__.__name__ == "UniqueConstraint"
        ]
        matching_constraints = [
            constraint
            for constraint in unique_constraints
            if tuple(constraint.fields)
            == ("image", "filter_spec", "focal_point_key")
        ]
        self.assertEqual(len(matching_constraints), 1)
        # Rendition identity must be unique for every image/filter/focal-key
        # combination; a conditional constraint would leave duplicate rows
        # possible for part of the published model state.
        self.assertIsNone(matching_constraints[0].condition)

    def test_document_has_only_native_minimum_contract(self):
        self.assertEqual(
            {field.name for field in self.Document._meta.local_fields},
            {
                "id",
                "title",
                "file",
                "created_at",
                "uploaded_by_user",
                "file_size",
                "file_hash",
                "collection",
            },
        )
        self.assertFalse(
            any("blog" in field.name.lower() for field in self.Document._meta.fields)
        )

    def test_project_apps_have_no_duplicate_labels_or_legacy_blog_dependency(self):
        project_apps = [
            app
            for app in self.apps.get_app_configs()
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
        self.assertEqual(
            len({app.label for app in project_apps}), len(project_apps)
        )
        self.assertEqual(
            {model._meta.label for model in self.apps.get_app_config("resources").get_models()},
            {"resources.Image", "resources.Rendition", "resources.Document"},
        )
        # 精确匹配旧包/业务模块边界，不能将合法根包 wagtailblog2 误判为 Blog。
        # 检查全部已注册 App，避免旧包被 project_apps 的新站前缀过滤掉。
        forbidden_packages = (
            "wagtailblog3",
            "blog",
            "wagtailblog2.apps.blog",
            "wagtailblog2.apps.guides",
        )
        self.assertFalse(
            any(
                app.name == package or app.name.startswith(package + ".")
                for app in self.apps.get_app_configs()
                for package in forbidden_packages
            )
        )
        self.assertEqual(
            list((self.root / "src/wagtailblog2").rglob("migrations")), []
        )

    def test_resource_setup_did_not_open_database(self):
        from django.db import connections

        self.assertTrue(GUARD.active)
        self.assertTrue(all(connection.connection is None for connection in connections.all()))
        self.assertEqual(
            GUARD.violations,
            self.setup_violations_after,
            f"Unexpected resource setup IO entries: {GUARD.events[self.setup_violations_before:]}",
        )


if __name__ == "__main__":
    unittest.main()
