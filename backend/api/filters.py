"""Кастомные фильтры для API проекта Фудграм."""

import django_filters
from django.contrib.auth import get_user_model
from recipes.models import Ingredient, Recipe, Tag

User = get_user_model()


class IngredientFilter(django_filters.FilterSet):
    """Фильтрация ингредиентов по названию (поиск с начала строки)."""

    name = django_filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(django_filters.FilterSet):
    """Фильтрация рецептов по тегам, автору, избранному и корзине покупок."""

    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    author = django_filters.ModelChoiceFilter(queryset=User.objects.all())
    is_favorited = django_filters.NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = django_filters.NumberFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        """Фильтрует рецепты, добавленные пользователем в избранное."""
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтрует рецепты, добавленные пользователем в список покупок."""
        if value and self.request.user.is_authenticated:
            return queryset.filter(shopping_carts__user=self.request.user)
        return queryset
