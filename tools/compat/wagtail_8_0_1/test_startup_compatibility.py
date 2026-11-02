"""隔离启动合同：导入项目之前安装无 IO 守卫；不发送信号或写数据库。"""
import filesystem_boundary
import os, sys
from pathlib import Path
# 仓库入口自动定位；filesystem_boundary 先禁止本地文件变更。
REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO))
from tools.e2_no_io_guard import install_no_io_guard
GUARD=install_no_io_guard()
assert 'django' not in sys.modules
assert 'wagtailblog2.settings.dev' not in sys.modules
print('PREIMPORT_GUARD active=True django_loaded=False project_settings_loaded=False',flush=True)
import json, unittest, importlib.metadata
from unittest.mock import patch
AUXILIARY='--locales' in sys.argv
if AUXILIARY: sys.argv.remove('--locales')
sys.path.insert(0,str(REPO/'src'))
os.environ['DJANGO_SETTINGS_MODULE']='blocker01_locales_settings' if AUXILIARY else 'wagtailblog2.settings.dev'
print('ENVIRONMENT',json.dumps({'executable':sys.executable,'wagtail':importlib.metadata.version('wagtail'),'settings':os.environ['DJANGO_SETTINGS_MODULE'],'auxiliary_locales':AUXILIARY}),flush=True)

def live_receivers(signal,sender):
    """Inspect the real connected callables without invoking database-writing signals."""
    sync,async_=signal._live_receivers(sender)
    return [*sync,*async_]

class StartupCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import django
        before=GUARD.violations
        try:
            with patch('modelsearch.backends.database.sqlite.utils.fts5_available',return_value=False) as fts5, patch('socket.has_ipv6',False):
                django.setup()
            assert fts5.called, 'Expected existing modelsearch capability probe'
            from django.apps import apps
            assert apps.ready and apps.apps_ready and apps.models_ready
            print('DJANGO_SETUP_COMPLETED apps_ready=True models_ready=True',flush=True)
        finally:
            print('WAGTAIL_LOADED_SOURCE',getattr(sys.modules.get('wagtail'),'__file__',None),flush=True)
            print('SETUP_GUARD',json.dumps({'active':GUARD.active,'violations':GUARD.violations,'delta':GUARD.violations-before,'events':GUARD.events}),flush=True)
            assert GUARD.active and GUARD.violations==before==0

    def tearDown(self):
        from django.db import connections
        self.assertTrue(GUARD.active)
        self.assertEqual(GUARD.violations,0,GUARD.events)
        self.assertTrue(all(c.connection is None for c in connections.all()))
        self.assertNotIn('wagtail.api.v3.api',sys.modules)

    def test_01_actual_startup_and_settings_scope(self):
        from django.apps import apps
        from django.conf import settings
        self.assertTrue(apps.ready and apps.models_ready)
        self.assertEqual(settings.SETTINGS_MODULE,os.environ['DJANGO_SETTINGS_MODULE'])
        self.assertEqual(apps.is_installed('wagtail.locales'),AUXILIARY)
        if AUXILIARY:
            from wagtail.locales.apps import WagtailLocalesAppConfig
            self.assertIsInstance(apps.get_app_config('wagtaillocales'),WagtailLocalesAppConfig)
        else:
            self.assertFalse(apps.is_installed('wagtail.locales'))
        self.assertFalse(apps.is_installed('wagtail.api.v3'))

    def test_02_api_module_absent_and_no_mounted_api_route(self):
        from django.conf import settings
        from django.urls import get_resolver,resolve,URLResolver
        from wagtail import views as wagtail_views
        self.assertNotIn('wagtail.api.v3.api',sys.modules)
        self.assertIs(resolve('/api/v3/').func,wagtail_views.serve)
        def walk(patterns):
            for item in patterns:
                if isinstance(item,URLResolver):
                    yield from walk(item.url_patterns)
                else:
                    yield item
        visited=0
        for p in walk(get_resolver(settings.ROOT_URLCONF).url_patterns):
            visited+=1
            callback_module=getattr(p.callback,'__module__','')
            self.assertFalse(callback_module.startswith(('wagtail.api.v3','ninja.')),callback_module)
        self.assertGreater(visited,0)
        self.assertNotIn('wagtail.api.v3.api',sys.modules)
        print('ROUTES_INSPECTED',visited,flush=True)

    def test_03_redirect_permission_policy_is_registered(self):
        from wagtail.contrib.redirects.models import Redirect
        from wagtail.permissions import policy_registry
        from wagtail.permission_policies import ModelPermissionPolicy
        policy=policy_registry.get_by_type(Redirect,fallback=False)
        self.assertIsInstance(policy,ModelPermissionPolicy)
        self.assertIs(policy.model,Redirect)
        self.assertIsNone(policy_registry.get_fallback_policy(Redirect))

    def test_04_redirect_page_move_receiver_is_connected(self):
        from wagtail.signals import post_page_move
        from wagtail.contrib.redirects.signal_handlers import autocreate_redirects_on_page_move
        self.assertIn(autocreate_redirects_on_page_move,live_receivers(post_page_move,None))

    def test_05_redirect_slug_change_receiver_is_connected(self):
        from wagtail.signals import page_slug_changed
        from wagtail.contrib.redirects.signal_handlers import autocreate_redirects_on_slug_change
        self.assertIn(autocreate_redirects_on_slug_change,live_receivers(page_slug_changed,None))

    def test_06_custom_document_actual_collection_permission_policy(self):
        from django.apps import apps
        from django.contrib.auth.models import AnonymousUser
        from wagtail.documents import get_document_model
        from wagtail.permission_policies.collections import CollectionOwnershipPermissionPolicy
        from wagtail.permissions import policy_registry
        document=get_document_model()
        self.assertIs(document,apps.get_model('resources','Document'))
        policy=policy_registry.get_by_type(document,fallback=False)
        self.assertIsInstance(policy,CollectionOwnershipPermissionPolicy)
        self.assertIs(policy.model,document)
        self.assertIs(policy.auth_model,apps.get_model('wagtaildocs','Document'))
        self.assertEqual(policy.owner_field_name,'uploaded_by_user')
        self.assertIsNone(policy_registry.get_fallback_policy(document))
        self.assertFalse(policy.user_has_permission(AnonymousUser(),'change'))

    def test_07_custom_document_reference_index_and_receivers(self):
        from django.db.models.signals import post_save,post_delete
        from wagtail.documents import get_document_model
        from wagtail.models.reference_index import ReferenceIndex
        from wagtail.signal_handlers import update_reference_index_on_save,remove_reference_index_on_delete
        document=get_document_model()
        self.assertIn(document,ReferenceIndex.indexed_models)
        self.assertIn(document,ReferenceIndex.tracked_models)
        self.assertTrue(ReferenceIndex.is_indexed(document))
        self.assertIn(update_reference_index_on_save,live_receivers(post_save,document))
        self.assertIn(remove_reference_index_on_delete,live_receivers(post_delete,document))

    def test_08_custom_document_storage_cleanup_receiver(self):
        from django.db.models.signals import post_delete
        from wagtail.documents import get_document_model
        from wagtail.documents.signal_handlers import post_delete_file_cleanup
        self.assertIn(post_delete_file_cleanup,live_receivers(post_delete,get_document_model()))

    def test_09_custom_document_display_class_lookup(self):
        from django.db.models import ForeignKey,CASCADE
        from wagtail.admin.ui.fields import display_class_registry
        from wagtail.documents import get_document_model
        from wagtail.documents.components import DocumentDisplay
        field=ForeignKey(get_document_model(),on_delete=CASCADE)
        self.assertIs(display_class_registry.get(field),DocumentDisplay)

    def test_10_snippets_post_migrate_receiver_for_real_appconfig(self):
        from django.apps import apps
        from django.db.models.signals import post_migrate
        from wagtail.snippets.models import create_extra_permissions
        config=apps.get_app_config('wagtailsnippets')
        self.assertIn(create_extra_permissions,live_receivers(post_migrate,config))

    def test_11_native_locale_model_home_relation_and_registered_policy(self):
        from django.apps import apps
        from wagtail.models import Locale,Page
        from wagtail.permissions import policy_registry,locale_permission_policy
        from wagtail.permission_policies import ModelPermissionPolicy
        home=apps.get_model('site_home','HomePage')
        self.assertIs(apps.get_model('wagtailcore','Locale'),Locale)
        self.assertIs(home._meta.get_field('locale').remote_field.model,Locale)
        self.assertIs(Page._meta.get_field('locale').remote_field.model,Locale)
        policy=policy_registry.get_by_type(Locale,fallback=False)
        self.assertIs(policy,locale_permission_policy)
        self.assertIsInstance(policy,ModelPermissionPolicy)
        self.assertIs(policy.model,Locale)
        self.assertIsNone(policy_registry.get_fallback_policy(Locale))

    def test_12_native_site_policy_and_home_relation(self):
        from django.apps import apps
        from wagtail.models import Site,Page
        from wagtail.permissions import policy_registry,site_permission_policy
        self.assertIs(apps.get_model('wagtailcore','Site'),Site)
        self.assertIs(Site._meta.get_field('root_page').remote_field.model,Page)
        self.assertIs(policy_registry.get_by_type(Site,fallback=False),site_permission_policy)
        self.assertIs(site_permission_policy.model,Site)

    def test_13_custom_user_preserves_native_auth_group_permissions(self):
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import AbstractUser,Group,Permission
        user=get_user_model()
        self.assertEqual(user._meta.label,'site_identity.User')
        self.assertTrue(issubclass(user,AbstractUser))
        self.assertIs(user._meta.get_field('groups').remote_field.model,Group)
        self.assertIs(user._meta.get_field('user_permissions').remote_field.model,Permission)


    def test_14_custom_image_actual_collection_permission_policy(self):
        from django.apps import apps
        from django.contrib.auth.models import AnonymousUser
        from wagtail.images import get_image_model
        from wagtail.permission_policies.collections import CollectionOwnershipPermissionPolicy
        from wagtail.permissions import policy_registry
        image=get_image_model()
        self.assertIs(image,apps.get_model('resources','Image'))
        policy=policy_registry.get_by_type(image,fallback=False)
        self.assertIsInstance(policy,CollectionOwnershipPermissionPolicy)
        self.assertIs(policy.model,image)
        self.assertIs(policy.auth_model,apps.get_model('wagtailimages','Image'))
        self.assertEqual(policy.owner_field_name,'uploaded_by_user')
        self.assertIsNone(policy_registry.get_fallback_policy(image))
        self.assertFalse(policy.user_has_permission(AnonymousUser(),'change'))

    def test_15_custom_image_reference_index_and_receivers(self):
        from django.db.models.signals import post_save,post_delete
        from wagtail.images import get_image_model
        from wagtail.models.reference_index import ReferenceIndex
        from wagtail.signal_handlers import update_reference_index_on_save,remove_reference_index_on_delete
        image=get_image_model()
        self.assertIn(image,ReferenceIndex.indexed_models)
        self.assertIn(image,ReferenceIndex.tracked_models)
        self.assertTrue(ReferenceIndex.is_indexed(image))
        self.assertIn(update_reference_index_on_save,live_receivers(post_save,image))
        self.assertIn(remove_reference_index_on_delete,live_receivers(post_delete,image))

    def test_16_custom_image_display_registry_lookup(self):
        from django.db.models import ForeignKey,CASCADE
        from wagtail.admin.ui.fields import display_class_registry
        from wagtail.images import get_image_model
        from wagtail.images.components import ImageDisplay
        self.assertIs(display_class_registry.get(ForeignKey(get_image_model(),on_delete=CASCADE)),ImageDisplay)

    def test_17_custom_image_chooser_formfield_registration(self):
        from django.db.models import ForeignKey,CASCADE
        from wagtail.admin.forms.models import registry,formfield_for_dbfield
        from wagtail.images import get_image_model
        from wagtail.images.widgets import AdminImageChooser
        field=ForeignKey(get_image_model(),on_delete=CASCADE)
        self.assertIs(registry.get(field)['widget'],AdminImageChooser)
        formfield=formfield_for_dbfield(field)
        self.assertIsInstance(formfield.widget,AdminImageChooser)
        self.assertIs(formfield.widget.model,get_image_model())

    def test_18_custom_image_revision_comparison_registration(self):
        from django.db.models import ForeignKey,CASCADE
        from wagtail.admin.compare import comparison_class_registry
        from wagtail.images import get_image_model
        from wagtail.images.edit_handlers import ImageFieldComparison
        self.assertIs(comparison_class_registry.get(ForeignKey(get_image_model(),on_delete=CASCADE)),ImageFieldComparison)

    def test_19_custom_image_native_save_and_delete_receivers(self):
        from django.db.models.signals import post_save,post_delete
        from wagtail.images import get_image_model
        from wagtail.images.signal_handlers import post_save_image_feature_detection,post_delete_file_cleanup
        image=get_image_model()
        self.assertIn(post_save_image_feature_detection,live_receivers(post_save,image))
        self.assertIn(post_delete_file_cleanup,live_receivers(post_delete,image))

    def test_20_custom_rendition_native_cleanup_and_cache_receivers(self):
        from django.apps import apps
        from django.db.models.signals import post_delete
        from wagtail.images import get_image_model
        from wagtail.images.signal_handlers import post_delete_file_cleanup,post_delete_purge_rendition_cache
        rendition=get_image_model().get_rendition_model()
        self.assertIs(rendition,apps.get_model('resources','Rendition'))
        self.assertIn(post_delete_file_cleanup,live_receivers(post_delete,rendition))
        self.assertIn(post_delete_purge_rendition_cache,live_receivers(post_delete,rendition))

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(StartupCompatibilityTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    summary={'settings':os.environ['DJANGO_SETTINGS_MODULE'],'auxiliary_locales':AUXILIARY,'tests_planned':suite.countTestCases(),'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'guard_active':GUARD.active,'guard_violations':GUARD.violations,'guard_events':GUARD.events,'api_module_present':'wagtail.api.v3.api' in sys.modules}
    print('EXTRA_CONTRACT_SUMMARY',json.dumps(summary),flush=True)
    raise SystemExit(0 if result.wasSuccessful() and GUARD.active and GUARD.violations==0 else 1)
