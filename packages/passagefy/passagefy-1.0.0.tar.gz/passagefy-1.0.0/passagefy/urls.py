# encoding: utf-8
"""
@author: 代码厨子
@license: (C) Copyright 2020.
@contact: hofeng@aqifun.com
@software: Python 3
@file: urls.py
@time: 2023/10/17 10:23
@desc:
"""
from rest_framework.routers import DefaultRouter
import passagefy.admin as admin

passagefyAdminRouter = DefaultRouter()

passagefyAdminRouter.register(r'admin/attachment/config', admin.AdminAttachmentConfig, basename="AdminAttachmentConfig")
passagefyAdminRouter.register(r'admin/attachment/data', admin.AdminAttachmentViewSet, basename="AdminAttachmentViewSet")
passagefyAdminRouter.register(r'admin/feedback/config', admin.AdminFeedbackConfig, basename="AdminFeedbackConfig")
passagefyAdminRouter.register(r'admin/feedback/data', admin.AdminFeedbackViewSet, basename="AdminFeedbackViewSet")
