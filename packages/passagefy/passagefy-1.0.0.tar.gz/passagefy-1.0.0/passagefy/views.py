import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Feedback


@csrf_exempt
def passagefy_webhook(request):
    auth = request.headers.get('Authorization', "")
    body = json.loads(request.body.decode('utf-8'))
    settings.LOGGER.info(f"passagefy_webhook: {auth}\nbody: {body}")
    if auth == settings.PASSAGEFY_WEBHOOK_TOKEN:
        msg_id = body.get('msg_id', None)
        if msg_id:
            Feedback.objects.filter(msg_id=msg_id).update(status=body.get('status', ''), feishu_id=body.get('feishu_id', ''), completion_rate=body.get('completion_rate', 0))
    return JsonResponse({"code": 0, "msg": "success"})
