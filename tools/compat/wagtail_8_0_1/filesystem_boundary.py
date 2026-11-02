"""复现进程的只读文件边界：不再允许向原实验临时目录写入。"""

import os
import sys


def audit(event, args):
    if event == "open":
        _, mode, flags = args
        writing = (
            isinstance(mode, str) and any(char in mode for char in "wax+")
        ) or (
            isinstance(flags, int)
            and bool(
                flags
                & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
            )
        )
        if writing:
            raise PermissionError("compatibility reproduction forbids file writes")
    elif event in (
        "os.mkdir", "os.remove", "os.rmdir", "os.chmod", "os.utime",
        "os.truncate", "os.rename", "os.link", "os.symlink", "os.chown",
    ):
        raise PermissionError("compatibility reproduction forbids file mutations")


# 仅增加文件边界；数据库、网络、Storage、任务等仍由原 E2 守卫负责。
sys.dont_write_bytecode = True
sys.addaudithook(audit)
