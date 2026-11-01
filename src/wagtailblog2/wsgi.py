"""
WagtailBlog2 WSGI 部署入口.

边界原则 (ADR-P0-06)：
1. 仅暴露标准 application 可调用对象；
2. 自动注入 src 目录到 sys.path；
3. 默认加载 wagtailblog2.settings.dev。
"""

import os
import sys
from pathlib import Path
from typing import Any

from django.core.wsgi import get_wsgi_application

base_dir = Path(__file__).resolve().parent.parent.parent
src_dir = base_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wagtailblog2.settings.dev")

application: Any = get_wsgi_application()
