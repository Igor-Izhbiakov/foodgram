"""Настройка административной панели для приложения users."""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from users.models import Follow

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Управление пользователями в панели администратора."""

    list_display = (
        'id', 'email', 'username', 'first_name', 'last_name', 'is_staff'
    )
    search_fields = ('email', 'username')
    list_filter = ('is_staff', 'is_superuser', 'is_active')


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Управление подписками пользователей."""

    list_display = ('id', 'user', 'author')
    search_fields = ('user__username', 'author__username')

    def get_queryset(self, request):
        """Оптимизация запросов для списка подписок."""
        return super().get_queryset(request).select_related('user', 'author')
