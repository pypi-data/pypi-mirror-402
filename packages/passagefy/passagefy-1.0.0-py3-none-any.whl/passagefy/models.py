import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='passagefy_feedback_user', null=True, blank=True, verbose_name="用户")
    msg_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="系统 ID")
    body = models.TextField(verbose_name="反馈内容", max_length=200000)
    feishu_id = models.CharField(verbose_name="飞书ID", max_length=50, null=True, blank=True)
    completion_rate = models.FloatField(verbose_name="完成度", default=0)
    status = models.CharField(verbose_name="状态", max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = '反馈'
        verbose_name_plural = verbose_name
        ordering = ['-id']

    def __str__(self):
        return self.body


class Attachment(models.Model):
    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE, related_name='passagefy_feedback_attachments')
    file = models.FileField(verbose_name="附件")

    class Meta:
        verbose_name = '附件'
        verbose_name_plural = verbose_name
