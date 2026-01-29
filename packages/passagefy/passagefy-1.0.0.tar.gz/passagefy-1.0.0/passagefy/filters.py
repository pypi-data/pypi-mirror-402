# encoding: utf-8
"""
@author: 代码厨子
@license: (C) Copyright 2020.
@contact: hofeng@aqifun.com
@software: Python 3
@file: filters.py
@time: 2025/1/2 18:23
@desc:
"""
import datetime
import django_filters
from django.db.models import Q


class PubFilter(django_filters.rest_framework.FilterSet):
    def region_filter(self, queryset, name, value):
        """
        顶级行政区划ID方式
        """
        if not str(value) == '-1000':
            return queryset.filter(area__region__parent_id=value)
        return queryset

    def common_filter(self, queryset, name, value):
        """
        普通等于方式搜索
        """
        if str(value) == '-999':
            return queryset.filter(**{f"{name}__isnull": True})
        if not str(value) == '-1000':
            dic = {name: value}
            return queryset.filter(**dic)
        return queryset

    def keyword_filter(self, queryset, name, value):
        """
        关键词模糊方式
        """
        if not str(value) == '-1000':
            return queryset.filter(**{name + '__icontains': value})
        return queryset

    def many_filter(self, queryset, name, value):
        """
        多对多字段数组查询方式
        """
        if not str(value) == '-1000':
            if ',' in value:
                tags = value.split(',')
            else:
                tags = [value]
            return queryset.filter(**{name + '__id__in': tags})
        return queryset

    def center_filter(self, queryset, name, value):
        """
        取两个值中间方式
        """
        if not str(value) == '-1000':
            if ',' in value:
                tags = value.split(',')
                lte = name + '__lte'
                gte = name + '__gte'
                if '-' in value:
                    data = {
                        gte: datetime.datetime.strptime(tags[0], '%Y-%m-%d'),
                        lte: datetime.datetime.strptime(tags[1], '%Y-%m-%d')
                    }
                else:
                    data = {
                        gte: float(tags[0]),
                        lte: float(tags[1])
                    }
                return queryset.filter(**data)
        return queryset

    def empty_filter(self, queryset, name, value):
        return queryset

    def order_filter(self, queryset, name, value):
        return queryset.order_by(value)

    def user_filter(self, queryset, name, value: str):
        max_filter = Q()
        max_filter.connector = 'OR'
        if value.isdigit():
            max_filter.children.append((f"{name}__id", value))
        max_filter.children.append((f"{name}__username__icontains", value))
        max_filter.children.append((f"{name}__nickname__icontains", value))
        return queryset.filter(max_filter)

    @staticmethod
    def union_filter(queryset, name: str, value: str):
        _filter = Q()
        _filter.connector = 'OR'
        for item in name.split('-'):
            _filter.children.append((f"{item}__icontains", value))
        return queryset.filter(_filter)


class AdminBaseFilter(PubFilter):
    msg_id = django_filters.CharFilter(method='keyword_filter', help_text="系统 ID")
    body = django_filters.CharFilter(method='keyword_filter', help_text="反馈内容")
    feishu_id = django_filters.CharFilter(method='keyword_filter', help_text="飞书 ID")
