"""新站最小持久身份模型。"""

from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """最小 AbstractUser 扩展。

    首版只复用 Django/Wagtail 原生认证、组和权限能力，不添加会员或业务资料字段。
    真实迁移文件和数据库初始化在 P0-E3 授权后单独处理。
    """

    pass
