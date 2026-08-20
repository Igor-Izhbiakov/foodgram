"""Кастомные разрешения для API проекта Фудграм."""

from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Разрешает изменение контента только автору или администратору.

    Остальным пользователям доступен только просмотр.
    """

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or (
                request.user.is_authenticated
                and (obj.author == request.user or request.user.is_staff)
            )
        )
