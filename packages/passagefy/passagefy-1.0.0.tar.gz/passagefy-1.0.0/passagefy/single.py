import json

import requests
import threading
import hashlib

from django.conf import settings
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from .models import *


def webhook(obj: Feedback, method: str | None = None):
    url = settings.PASSAGEFY_WEBHOOK_URL
    token = settings.PASSAGEFY_WEBHOOK_TOKEN
    if not url:
        return False
    if not method:
        method: str = "update" if obj.feishu_id else "create"
    file_urls = list()
    for attachment in obj.passagefy_feedback_attachments.all():
        file_urls.append(attachment.file.url)
    data = {
        "method": method,
        "params": {
            "user": obj.user.username if obj.user else "",
            "msg_id": str(obj.msg_id),
            "body": obj.body,
            "feishu_id": obj.feishu_id or "",
            "file_urls": "\n".join(file_urls),
        }
    }
    json_data = json.dumps(data, ensure_ascii=False)
    headers = {
        "Content-Type": "application/json",
        "Client-Token": hashlib.md5(json_data.encode()).hexdigest()
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        res = requests.post(url, json=data, headers=headers)
    except Exception as e:
        settings.LOGGER.error(f"回调多维表格错误：{obj.id}\n{e}")
        return e
    if res.status_code == 200 and res.json()["code"] and not method == "delete":
        obj.status = res.json()["msg"]
        obj.save()
    return True


@receiver(post_save, sender=Feedback)
def post_save_feedback(**kwargs):
    obj: Feedback = kwargs['instance']
    threading.Thread(target=webhook, args=(obj,)).start()


@receiver(post_save, sender=Attachment)
def post_save_attachment(**kwargs):
    obj: Feedback = kwargs['instance'].feedback
    threading.Thread(target=webhook, args=(obj,)).start()


@receiver(pre_delete, sender=Feedback)
def pre_delete_feedback(**kwargs):
    obj: Feedback = kwargs['instance']
    webhook(obj, method="delete")
