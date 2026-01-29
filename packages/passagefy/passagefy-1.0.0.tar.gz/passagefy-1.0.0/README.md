# passagefy 「通途」 使用说明

我们结合飞书的多维表格，实现了一个基于Django的应用，帮助用户创建一个技术反馈表，并且与飞书的多维表格进行同步。

集成了HAdmin的配置文件生成功能，帮助前端进行渲染。

# 快速开始

## 安装

```bash
pip install passagefy
```

## 使用方式

- 在 settings.py 中添加 passagefy 到 INSTALLED_APPS 中

```python
INSTALLED_APPS = [
    ...,
    'passagefy'
]
```

- 并且设定两个变量，也放在settings.py中

```python
PASSAGEFY_WEBHOOK_URL = "用于发送给飞书多维表格的webhook地址"
PASSAGEFY_WEBHOOK_TOKEN = "用于验证的token，如果没设定，就不要这个"
```

**重点说明：token如果设定，那么接收和发送都是用相同的token，请注意配置飞书多维表格时设定好**

- 最后，在urls.py中添加如下代码

```python
from django.urls import path, include
from passagefy.urls import passagefyAdminRouter
from passagefy.views import passagefy_webhook

urlpatterns = [
    ...,
    path('v1/passagefy/', include(passagefyAdminRouter.urls)),  # HAdmin配置文件相关接口
    path('v1/passagefy/webhook', passagefy_webhook),  # 飞书多维表格同步接口
]
```

# 版本历史

1.0.0 初始版本