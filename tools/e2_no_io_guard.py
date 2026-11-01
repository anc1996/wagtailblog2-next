"""Opt-in, process-wide E2 tripwire; not an OS sandbox or full P0 acceptance.

Install before importing Django/project settings. An audit dispatcher catches
stdlib/native aliases; a temporary import finder patches framework/service APIs
only when imported. Uninstall restores patches and disables the dispatcher (Python
audit hooks themselves cannot be removed). Arguments/credentials are never logged.
"""

import importlib.abc
from pathlib import Path
import sys
from typing import NamedTuple


class E2IOViolation(RuntimeError):
    """A forbidden external-IO entry was reached under the E2 guard."""


class Violation(NamedTuple):
    category: str
    operation: str


_STORAGE_METHODS = (
    "open", "_open", "save", "_save", "delete", "exists", "listdir", "size",
    "path", "url", "get_accessed_time", "get_created_time", "get_modified_time",
)
_OPTIONAL_APIS = {
    "MySQLdb": (("", ("connect", "Connect"), "database"),),
    "pymysql": (("", ("connect", "Connect"), "database"),),
    "psycopg": (("", ("connect",), "database"),),
    "psycopg2": (("", ("connect",), "database"),),
    "oracledb": (("", ("connect", "connect_async"), "database"),),
    "celery.app.base": (("Celery", ("send_task",), "task"),),
    "celery.app.task": (("Task", ("delay", "apply", "apply_async"), "task"),),
    "kombu.messaging": (("Producer", ("publish",), "task"),),
}
_MISSING = object()


class _GuardedLoader:
    def __init__(self, loader, guard):
        self.loader = loader
        self.guard = guard

    def create_module(self, spec):
        create = getattr(self.loader, "create_module", None)
        return create(spec) if create else None

    def exec_module(self, module):
        self.loader.exec_module(module)
        self.guard._patch_module(module)

    def __getattr__(self, name):
        return getattr(self.loader, name)


class _GuardedImports(importlib.abc.MetaPathFinder):
    def __init__(self, guard):
        self.guard = guard

    def find_spec(self, fullname, path=None, target=None):
        if not (
            fullname in _OPTIONAL_APIS
            or fullname == "django.core.files.storage.base"
            or (fullname.startswith("django.db.backends.") and fullname.endswith(".base"))
        ):
            return None
        for finder in tuple(sys.meta_path):
            if finder is self:
                continue
            spec = finder.find_spec(fullname, path, target)
            if spec is not None:
                if spec.loader is not None:
                    spec.loader = _GuardedLoader(spec.loader, self.guard)
                return spec
        return None


class NoIOGuard:
    def __init__(self):
        self.active = False
        self.events = []
        self._patches = []
        self._finder = _GuardedImports(self)

    @property
    def violations(self):
        return len(self.events)

    def _deny(self, category, operation):
        self.events.append(Violation(category, operation))
        raise E2IOViolation(f"E2 no-external-IO violation: {category} ({operation})")

    def _blocked(self, category, operation):
        def blocked(*args, **kwargs):
            self._deny(category, operation)
        return blocked

    def _replace(self, owner, name, value):
        # Save descriptors verbatim; don't turn classmethods into bound methods.
        original = vars(owner).get(name, _MISSING)
        self._patches.append((owner, name, original))
        setattr(owner, name, value)

    def _patch_methods(self, owner, methods, category):
        for name in methods:
            if hasattr(owner, name):
                operation = f"{owner.__name__}.{name}"
                self._replace(owner, name, self._blocked(category, operation))

    def _patch_module(self, module):
        name = module.__name__
        if name == "django.core.files.storage.base":
            storage = module.Storage
            self._patch_methods(storage, _STORAGE_METHODS, "storage")

            def guard_subclass(cls, **kwargs):
                super(storage, cls).__init_subclass__(**kwargs)
                self._patch_methods(cls, _STORAGE_METHODS, "storage")

            # Also guards subsequently imported third-party/local overrides.
            self._replace(storage, "__init_subclass__", classmethod(guard_subclass))
        elif name.startswith("django.db.backends.") and name.endswith(".base"):
            for cls_name in ("BaseDatabaseWrapper", "DatabaseWrapper"):
                wrapper = getattr(module, cls_name, None)
                if wrapper is not None:
                    self._patch_methods(
                        wrapper, ("connect", "ensure_connection", "get_new_connection"),
                        "database",
                    )
        for owner_name, methods, category in _OPTIONAL_APIS.get(name, ()):
            owner = getattr(module, owner_name, None) if owner_name else module
            if owner is not None:
                self._patch_methods(owner, methods, category)

    def _audit(self, event, args):
        if not self.active:
            return
        if event.startswith("socket."):
            self._deny("network", event)
        if event in ("urllib.Request", "http.client.connect", "http.client.send"):
            self._deny("http", event)
        if event == "sqlite3.connect":
            self._deny("database", event)
        if event in (
            "subprocess.Popen", "os.system", "os.fork", "os.forkpty",
            "os.posix_spawn", "os.spawn", "os.exec", "pty.spawn",
        ):
            self._deny("process", event)

    def uninstall(self):
        """Restore Python patches; leave only an inert audit dispatcher."""
        if not self.active:
            return
        self.active = False
        sys.meta_path.remove(self._finder)
        for owner, name, original in reversed(self._patches):
            if original is _MISSING:
                delattr(owner, name)
            else:
                setattr(owner, name, original)
        self._patches.clear()
        sys.dont_write_bytecode = self._previous_bytecode


_GUARD = NoIOGuard()
_AUDIT_INSTALLED = False


def install_no_io_guard():
    """Install before framework/project imports; repeated active installs are safe."""
    global _AUDIT_INSTALLED
    if _GUARD.active:
        return _GUARD
    if any(
        name == "django" or name.startswith("django.")
        or name == "wagtailblog2" or name.startswith("wagtailblog2.")
        or name in _OPTIONAL_APIS
        for name in sys.modules
    ):
        raise RuntimeError(
            "E2 guard must be installed before Django/project/service-client imports"
        )
    if not _AUDIT_INSTALLED:
        sys.addaudithook(_GUARD._audit)
        _AUDIT_INSTALLED = True
    _GUARD._previous_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    sys.meta_path.insert(0, _GUARD._finder)
    _GUARD.active = True
    return _GUARD


def main():
    """Collect only the two approved test modules, after installing the guard."""
    if len(sys.argv) != 1:
        raise SystemExit("Usage: python -B -m tools.e2_no_io_guard")
    guard = install_no_io_guard()
    import unittest

    root = Path(__file__).resolve().parents[1]
    suite = unittest.TestSuite()
    for filename in (
        "test_e2_no_io_guard.py",
        "test_e2_bootstrap.py",
        "test_identity_contract.py",
    ):
        suite.addTests(unittest.defaultTestLoader.discover(str(root / "tests"), filename))
    if guard.violations:
        raise E2IOViolation("E2 test collection recorded a forbidden IO attempt")
    result = unittest.TextTestRunner(verbosity=2, failfast=True).run(suite)
    print(
        f"Guard probes + Mock-assisted skeleton only; violations={guard.violations}; "
        "SQLite FTS5 and socket IPv6 capabilities explicitly mocked unavailable. "
        "custom identity User verified; no media models or project migration graph verified. "
        "NOT full P0 E2."
    )
    return 0 if result.wasSuccessful() and guard.active else 1


if __name__ == "__main__":
    # Keep test imports on the same guard/exception identity as the module runner.
    sys.modules["tools.e2_no_io_guard"] = sys.modules[__name__]
    raise SystemExit(main())
