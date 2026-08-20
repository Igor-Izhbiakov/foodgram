"""Кастомные классы пагинации для API."""

from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """Пагинатор с поддержкой параметра limit."""

    page_size_query_param = 'limit'
    page_size = 6
