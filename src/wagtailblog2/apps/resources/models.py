"""公共资源最小模型；仅声明持久身份，不执行上传、派生生成或外部 IO。"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from taggit.managers import TaggableManager
from wagtail.documents.models import AbstractDocument, Document as WagtailDocument
from wagtail.images.models import AbstractImage, AbstractRendition, Image as WagtailImage


class Image(AbstractImage):
    """复用原生图片字段和后台表单，不依赖具体业务 Page。"""

    admin_form_fields = WagtailImage.admin_form_fields

    # TaggableManager 不采用 Meta.default_related_name，须显式区分反向名称。
    tags = TaggableManager(
        help_text=None, blank=True, verbose_name=_("tags"),
        related_name="resources_image_set",
    )

    class Meta(AbstractImage.Meta):
        # 原生具体 Image 仍在 registry 中；区分上传者的默认反向关系。
        default_related_name = "resources_image_set"


class Rendition(AbstractRendition):
    """派生图归属公共 Image，保留原生反向关系及三字段唯一性。"""

    image = models.ForeignKey(
        Image, related_name="renditions", on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("image", "filter_spec", "focal_point_key"),
                name="resources_rendition_image_filter_focal_unique",
            ),
        ]


class Document(AbstractDocument):
    """仅固定文档最小身份；交付、上传和下载业务不在本切片实现。"""

    admin_form_fields = WagtailDocument.admin_form_fields

    tags = TaggableManager(
        help_text=None, blank=True, verbose_name=_("tags"),
        related_name="resources_document_set",
    )

    class Meta(AbstractDocument.Meta):
        # 保留原生字段，只避免与 wagtaildocs.Document 的反向名称冲突。
        default_related_name = "resources_document_set"
