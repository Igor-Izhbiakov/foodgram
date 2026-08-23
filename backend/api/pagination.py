"""Кастомные классы пагинации для API."""

from django.conf import settings
from rest_framework.pagination import PageNumberPagination


class RecipePageNumberPagination(PageNumberPagination):
    """Пагинатор с поддержкой параметра limit."""

    page_size_query_param = 'limit'
    page_size = settings.DEFAULT_PAGE_SIZE
