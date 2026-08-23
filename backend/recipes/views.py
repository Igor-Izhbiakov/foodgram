"""Представления для приложения рецептов."""

from django.shortcuts import redirect
from recipes.models import Recipe


def redirect_short_link(request, pk):
    """Перенаправляет пользователя с короткой ссылки на страницу рецепта."""
    try:
        Recipe.objects.get(id=pk)
        return redirect(f'/recipes/{pk}/')
    except Recipe.DoesNotExist:
        return redirect('/404')
