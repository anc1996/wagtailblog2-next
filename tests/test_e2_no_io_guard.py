"""Negative probes. Install before unittest collection or any Django import."""

from tools.e2_no_io_guard import E2IOViolation, install_no_io_guard

GUARD = install_no_io_guard()

import http.client
import importlib
import os
from pathlib import Path
import runpy
import socket
import sqlite3
import subprocess
import sys
import unittest
from unittest.mock import patch
import urllib.request


_ALLOW_LOCAL_SOCKET_CREATION = False


def _probe_safety_net(event, args):
    """Fail safely if the guard under test ever lets a dangerous probe through."""
    if event == "open":
        mode, flags = args[1:3]
        if (mode and any(char in mode for char in "wax+")) or flags & (
            os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
        ):
            raise AssertionError("E2 negative probes must never write local files")
    if event == "socket.__new__" and _ALLOW_LOCAL_SOCKET_CREATION:
        return
    if (
        event.startswith("socket.")
        or event in {
            "sqlite3.connect", "urllib.Request", "http.client.connect",
            "http.client.send", "subprocess.Popen", "os.system", "os.fork",
            "os.forkpty", "os.posix_spawn", "os.spawn", "os.exec", "pty.spawn",
            "os.mkdir", "os.remove", "os.rename", "os.rmdir", "os.truncate",
        }
    ):
        raise AssertionError(f"E2 guard missed negative probe: {event}")


# Runs after the production audit dispatcher. A correct guard raises first.
# Unlike the guard under test, this test-only safety net is never uninstalled.
sys.addaudithook(_probe_safety_net)


class NoIOGuardTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(GUARD.active, "Do not execute probes without an active guard")
        self._before = GUARD.violations
        self._expected_violations = 0

    def tearDown(self):
        self.assertEqual(
            GUARD.violations - self._before, self._expected_violations,
            "Unexpected IO attempt outside an explicit negative probe",
        )

    def assert_blocked(self, operation, category):
        self.assertTrue(GUARD.active, "Do not execute probes without an active guard")
        before = GUARD.violations
        with self.assertRaises(E2IOViolation) as caught:
            operation()
        self._expected_violations += 1
        self.assertEqual(GUARD.violations, before + 1)
        self.assertEqual(GUARD.events[-1].category, category)
        self.assertIn("E2", str(caught.exception))
        self.assertNotIn("do-not-log-this", str(caught.exception))

    def test_00_install_is_idempotent_and_does_not_import_django(self):
        # Collection must remain framework-free, not merely settings-free.
        self.assertNotIn("django", sys.modules)
        self.assertIs(install_no_io_guard(), GUARD)
        self.assertTrue(GUARD.active)

    def test_01_uninstall_restores_runtime_and_rejects_late_install(self):
        global _ALLOW_LOCAL_SOCKET_CREATION
        original_connect = sqlite3.connect
        GUARD.uninstall()
        try:
            self.assertFalse(GUARD.active)
            self.assertIs(sqlite3.connect, original_connect)
            # Object creation is safe locally; no connect/bind/listen is attempted.
            _ALLOW_LOCAL_SOCKET_CREATION = True
            try:
                with socket.socket():
                    pass
            finally:
                _ALLOW_LOCAL_SOCKET_CREATION = False
            for name in ("django", "wagtailblog2.settings.dev", "psycopg2"):
                with patch.dict(sys.modules, {name: object()}):
                    with self.assertRaisesRegex(RuntimeError, "before|导入前"):
                        install_no_io_guard()
        finally:
            self.assertIs(install_no_io_guard(), GUARD)

    def _probe_manage_first_import(self, argv, expected_guard):
        # Stop at the first Django import, without loading settings or running
        # the actual framework. This observes startup ordering in a clean state.
        import importlib.abc

        self.assertNotIn("django", sys.modules)

        class StopBeforeDjango(Exception):
            pass

        test = self

        class Probe(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if fullname == "django":
                    test.assertEqual(GUARD.active, expected_guard)
                    raise StopBeforeDjango

        GUARD.uninstall()
        finder = Probe()
        sys.meta_path.insert(0, finder)
        try:
            with patch.object(sys, "argv", argv):
                with self.assertRaises(StopBeforeDjango):
                    runpy.run_path(
                        str(Path(__file__).resolve().parents[1] / "manage.py"),
                        run_name="__main__",
                    )
        finally:
            sys.meta_path.remove(finder)
            install_no_io_guard()

    def test_02_guarded_manage_installs_before_first_django_import(self):
        self._probe_manage_first_import(["manage.py", "--e2-no-io", "check"], True)

    def test_03_plain_manage_does_not_enable_guard(self):
        self._probe_manage_first_import(["manage.py", "check"], False)

    def test_local_source_and_configuration_reads_are_allowed(self):
        before = GUARD.violations
        root = Path(__file__).resolve().parents[1]
        self.assertIn("def main", (root / "manage.py").read_text(encoding="utf-8"))
        self.assertIn("[project]", (root / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(GUARD.violations, before)

    def test_socket_creation_is_blocked(self):
        self.assert_blocked(socket.socket, "network")

    def test_dns_is_blocked(self):
        self.assert_blocked(
            lambda: socket.getaddrinfo("do-not-log-this.invalid", 443), "network"
        )

    def test_connection_helper_is_blocked(self):
        self.assert_blocked(
            lambda: socket.create_connection(("127.0.0.1", 9), timeout=0.01),
            "network",
        )

    def test_sqlite_connection_and_native_alias_are_blocked(self):
        import _sqlite3

        for connect in (sqlite3.connect, sqlite3.dbapi2.connect, _sqlite3.connect):
            with self.subTest(connect=connect):
                self.assert_blocked(lambda: connect(":memory:"), "database")

    def test_http_request_is_blocked_before_network(self):
        self.assert_blocked(
            lambda: urllib.request.urlopen(
                "http://do-not-log-this.invalid/private?token=do-not-log-this"
            ),
            "http",
        )

    def test_direct_http_connection_is_blocked(self):
        self.assert_blocked(
            lambda: http.client.HTTPConnection("do-not-log-this.invalid").connect(),
            "http",
        )

    def test_subprocess_is_blocked(self):
        self.assert_blocked(
            lambda: subprocess.Popen(["e2-never-execute-do-not-log-this"]),
            "process",
        )

    def test_shell_is_blocked(self):
        self.assert_blocked(lambda: os.system("do-not-log-this"), "process")

    @unittest.skipUnless(hasattr(os, "fork"), "POSIX-only process entry")
    def test_fork_is_blocked(self):
        self.assert_blocked(os.fork, "process")

    @unittest.skipUnless(hasattr(os, "posix_spawn"), "POSIX-only process entry")
    def test_posix_spawn_is_blocked(self):
        self.assert_blocked(
            lambda: os.posix_spawn("e2-never-execute", ["e2-never-execute"], {}),
            "process",
        )

    def test_django_database_connection_is_blocked_before_backend(self):
        from django.db.backends.sqlite3.base import DatabaseWrapper

        wrapper = DatabaseWrapper({"NAME": ":memory:", "OPTIONS": {}}, alias="e2-no-io")
        self.assert_blocked(wrapper.connect, "database")
        self.assertIsNone(wrapper.connection)

    def test_storage_base_and_local_overrides_are_blocked(self):
        from django.core.files.storage import FileSystemStorage, Storage
        from django.core.files.storage.memory import InMemoryStorage

        # Its constructor itself calls path(); allocate without invoking that
        # already-forbidden operation, so the other entry points can be probed.
        memory_storage = object.__new__(InMemoryStorage)
        for storage in (Storage(), FileSystemStorage(), memory_storage):
            for name, args in (
                ("open", ("do-not-log-this",)),
                ("save", ("do-not-log-this", None)),
                ("exists", ("do-not-log-this",)),
                ("delete", ("do-not-log-this",)),
                ("listdir", ("do-not-log-this",)),
                ("size", ("do-not-log-this",)),
                ("path", ("do-not-log-this",)),
                ("url", ("do-not-log-this",)),
                ("get_modified_time", ("do-not-log-this",)),
            ):
                with self.subTest(storage=type(storage).__name__, method=name):
                    self.assert_blocked(
                        lambda: getattr(storage, name)(*args), "storage"
                    )

    def test_optional_driver_and_task_imports_are_guarded_without_loading_them(self):
        # Exercise the deferred import boundary with an in-memory module loader.
        # No optional service library is installed/imported and no task is sent.
        import importlib.abc
        import importlib.util
        import types

        class Loader(importlib.abc.Loader):
            def create_module(self, spec):
                return None

            def exec_module(self, module):
                def unsafe(*args, **kwargs):
                    raise AssertionError("guard failed to replace service entry")

                module.connect = unsafe
                module.Celery = type("Celery", (), {"send_task": unsafe})

        class Finder(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if fullname in {"psycopg2", "celery.app.base"}:
                    return importlib.util.spec_from_loader(fullname, Loader())

        packages = {}
        for name in ("celery", "celery.app"):
            packages[name] = types.ModuleType(name)
            packages[name].__path__ = []
        finder = Finder()
        # The guard's finder must wrap the following ordinary finder.
        sys.meta_path.insert(1, finder)
        try:
            with patch.dict(sys.modules, packages):
                for name, entry, category in (
                    ("psycopg2", "connect", "database"),
                    ("celery.app.base", "Celery", "task"),
                ):
                    with self.subTest(module=name):
                        module = importlib.import_module(name)
                        operation = getattr(module, entry)
                        if category == "task":
                            operation = operation().send_task
                        self.assert_blocked(operation, category)
        finally:
            sys.meta_path.remove(finder)

    def test_manage_guarded_check_strips_flag_before_dispatch(self):
        import manage
        from django.core.management import execute_from_command_line

        seen = []

        def execute(argv):
            seen.append(list(argv))
            self.assertTrue(GUARD.active)

        with patch.object(sys, "argv", ["manage.py", "--e2-no-io", "check"]):
            with patch("django.core.management.execute_from_command_line", execute):
                manage.main()
        self.assertEqual(seen, [["manage.py", "check"]])
        self.assertIsNotNone(execute_from_command_line)

    def test_manage_check_fails_even_if_command_catches_violation(self):
        import manage

        def execute(argv):
            self.assert_blocked(lambda: sqlite3.connect(":memory:"), "database")

        with patch.object(sys, "argv", ["manage.py", "--e2-no-io", "check"]):
            with patch("django.core.management.execute_from_command_line", execute):
                with self.assertRaises(E2IOViolation):
                    manage.main()

    def test_manage_rejects_unapproved_guarded_commands_before_dispatch(self):
        import manage

        with patch.object(sys, "argv", ["manage.py", "--e2-no-io", "shell"]):
            with patch("django.core.management.execute_from_command_line") as execute:
                with self.assertRaisesRegex(SystemExit, "check"):
                    manage.main()
                execute.assert_not_called()

if __name__ == "__main__":
    unittest.main()
