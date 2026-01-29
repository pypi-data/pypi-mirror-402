from django.db.models import Q
from hadmin.mixins import *
from rest_framework import serializers, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .filters import AdminBaseFilter

from .models import *


class AdminPagination(PageNumberPagination):
    """
    基础分页器
    """
    page_size = 20
    page_size_query_param = 'pageSize'
    page_query_param = "current"
    max_page_size = 5000


class BaseViewSet(viewsets.GenericViewSet):
    """
    基础视图，绑定权限
    """
    pagination_class = AdminPagination
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    config_class = None

    def get_serializer_class(self):
        if not self.config_class:
            return self.serializer_class
        if self.action == 'list':
            return self.config_class.list_class
        if self.action == 'retrieve':
            return self.config_class.read_class
        return self.config_class.create_class if self.config_class.create_class else self.config_class.read_class


#########################################################################################################################
class AdminAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = '__all__'


class AdminAttachmentConfig(PageConfigMixin, BaseViewSet):
    list_class = AdminAttachmentSerializer
    read_class = AdminAttachmentSerializer
    create_class = AdminAttachmentSerializer
    filter_class = AdminBaseFilter


class AdminAttachmentViewSet(ListModelMixin, RetrieveModelMixin, CreateModelMixin, UpdateModelMixin, DestroyModelMixin, BaseViewSet):
    queryset = Attachment.objects.all()
    config_class = AdminAttachmentConfig
    filterset_class = AdminAttachmentConfig.filter_class


#########################################################################################################################
class AdminFeedbackListSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = Feedback
        fields = ["id", "user", "completion_rate", "body", "status", "feishu_id", "created_at"]
        custom = {
            "completion_rate": {"method": "Progress"},
            "user": {"width": 120},
            "status": {"width": 120},
            "feishu_id": {"width": 120},
            "created_at": {"width": 120},
        }


class AdminFeedbackReadSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    passagefy_feedback_attachments = AdminAttachmentSerializer(many=True)

    class Meta:
        model = Feedback
        fields = '__all__'
        custom = {
            "completion_rate": {"method": "Progress"},
        }


class AdminFeedbackCreateSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Feedback
        fields = ["id", "user", "body"]
        inlines = {
            "passagefy_feedback_attachments": {
                "class": AdminAttachmentSerializer,
                "api": "/passagefy/admin/attachment/data/",
                "limit": 50,
                "field": "feedback",
            }
        }


class AdminFeedbackConfig(PageConfigMixin, BaseViewSet):
    list_class = AdminFeedbackListSerializer
    read_class = AdminFeedbackReadSerializer
    create_class = AdminFeedbackCreateSerializer
    filter_class = AdminBaseFilter


class AdminFeedbackViewSet(ListModelMixin, RetrieveModelMixin, CreateModelMixin, UpdateModelMixin, DestroyModelMixin, BaseViewSet):
    config_class = AdminFeedbackConfig
    filterset_class = AdminFeedbackConfig.filter_class

    def get_queryset(self):
        return Feedback.objects.filter(Q(user__isnull=True) | Q(user=self.request.user))
