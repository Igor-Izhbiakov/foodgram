"""Модуль с кастомными описаниями ошибок"""

from django.http import Http404
from rest_framework.views import exception_handler
from rest_framework.exceptions import NotFound, PermissionDenied


def custom_exception_handler(exc, context):
    """Кастомный обработчик ошибок для локализации ответов API."""
    if isinstance(exc, Http404):
        exc = NotFound(detail='Страница не найдена.')
    response = exception_handler(exc, context)

    if response is not None:
        if isinstance(exc, NotFound):
            response.data['detail'] = 'Страница не найдена.'
        elif isinstance(exc, PermissionDenied):
            response.data['detail'] = (
                'У вас недостаточно прав для '
                'выполнения данного действия.'
            )

    return response
