"""首页最小 Page 模型；发布生命周期完全交给 Wagtail 原生实现。"""

from wagtail.models import Page


class HomePage(Page):
    """首版首页身份骨架，不承载业务字段或自定义发布状态。"""

    # 不设置 parent_page_types/subpage_types，避免在 Blog/Guide 尚未批准前
    # 把未来页面类型永久写入首页合同；Wagtail 会按默认规则解析页面树。
    pass
