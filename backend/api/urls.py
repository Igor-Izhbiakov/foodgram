"""Маршрутизация эндпоинтов для приложения api."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (
    FoodgramUserViewSet,
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet,
    redirect_short_link,
)

router = DefaultRouter()
router.register('users', FoodgramUserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('s/<int:pk>/', redirect_short_link, name='short_link'),
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
