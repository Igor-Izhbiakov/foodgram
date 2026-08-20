"""Настройка административной панели для приложения recipes."""

from django.contrib import admin
from django.db.models import Count
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)


class RecipeIngredientInline(admin.TabularInline):
    """Позволяет добавлять ингредиенты прямо на странице рецепта."""

    model = RecipeIngredient
    min_num = 1
    extra = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Управление тегами в админке."""

    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Управление ингредиентами с быстрым поиском по названию."""

    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Управление рецептами с отображением числа добавлений в избранное."""

    list_display = ('id', 'name', 'author', 'get_favorites_count')
    list_filter = ('tags', 'author')
    search_fields = ('name', 'author__username', 'author__email')
    inlines = (RecipeIngredientInline,)

    def get_queryset(self, request):
        """Оптимизация запросов: предзагрузка авторов и подсчет избранного."""
        queryset = super().get_queryset(request)
        return queryset.select_related('author').annotate(
            favorites_count=Count('favorites')
        )

    @admin.display(
        description='В избранном (раз)',
        ordering='favorites_count'
    )
    def get_favorites_count(self, obj):
        """Возвращает количество добавлений рецепта в избранное."""
        return obj.favorites_count


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Администрирование избранных рецептов."""

    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')

    def get_queryset(self, request):
        """Оптимизация запросов для списка избранного."""
        return super().get_queryset(request).select_related('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Администрирование списков покупок."""

    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')

    def get_queryset(self, request):
        """Оптимизация запросов для списка корзины покупок."""
        return super().get_queryset(request).select_related('user', 'recipe')
