#!/usr/bin/env python
"""
WagtailBlog2 命令行管理脚本 (manage.py).

边界与生命周期原则：
1. 仅面向独立新站架构，默认加载 wagtailblog2.settings.dev；
2. 自动将 src 目录注入 sys.path，保证 Python 根包 wagtailblog2 导入解析一致；
3. 仅 --e2-no-io check 显式安装导入前守卫；普通 check 不是完整 P0 E2；
4. 未获授权不得执行迁移、启动服务或连接外部服务。
"""

import os
import sys
from pathlib import Path


def main() -> None:
    """运行 Django 命令行管理任务."""
    argv = list(sys.argv)
    guard = None
    if "--e2-no-io" in argv:
        argv.remove("--e2-no-io")
        if argv[1:] != ["check"]:
            raise SystemExit("E2 路径仅允许 --e2-no-io check")
        from tools.e2_no_io_guard import install_no_io_guard

        guard = install_no_io_guard()
        violations_before = guard.violations

    # 将 src 目录显式加入模块搜索路径，保证包导入的一致性
    base_dir = Path(__file__).resolve().parent
    src_dir = base_dir / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wagtailblog2.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "无法导入 Django。请确认已在 wagtailblog-test 虚拟环境中安装相关依赖，"
            "且 sys.path 包含项目根包。"
        ) from exc
    execute_from_command_line(argv)
    if guard is not None and guard.violations != violations_before:
        from tools.e2_no_io_guard import E2IOViolation

        raise E2IOViolation("E2 check recorded a forbidden IO attempt")


if __name__ == "__main__":
    main()
