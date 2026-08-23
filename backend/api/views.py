"""Представления API для управления рецептами и пользователями Foodgram."""

from django.contrib.auth import get_user_model
from django.db.models import Count, Exists, OuterRef, Prefetch, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeShortSerializer,
    RecipeWriteSerializer,
    TagSerializer,
    UserAvatarSerializer,
    UserSerializer,
    UserSubscriptionSerializer,
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Follow

User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для просмотра тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для просмотра ингредиентов с поиском по названию."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для управления рецептами, избранным и списком покупок."""

    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        """Возвращает кверисет рецептов с аннотацией флагов."""
        user = self.request.user
        queryset = Recipe.objects.all()
        authors_queryset = User.objects.all()
        if user.is_authenticated:
            authors_queryset = authors_queryset.annotate(
                is_subscribed=Exists(
                    Follow.objects.filter(user=user, author=OuterRef('pk'))
                )
            )
            queryset = queryset.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(user=user, recipe=OuterRef('pk'))
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=user, recipe=OuterRef('pk')
                    )
                )
            )

        if self.action in ('list', 'retrieve'):
            return queryset.select_related('author').prefetch_related(
                'tags', 'recipe_ingredients__ingredient'
            )
        return queryset

    def get_serializer_class(self):
        """Выбирает сериализатор для чтения или записи."""
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def add_to_list(self, model, user, pk):
        """Вспомогательный метод для добавления рецепта в списки."""

        recipe = get_object_or_404(Recipe, id=pk)
        _, created = model.objects.get_or_create(user=user, recipe_id=pk)
        if not created:
            return Response(
                {'errors': 'Рецепт уже добавлен в этот список!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = RecipeShortSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def remove_from_list(self, model, user, pk):
        """Вспомогательный метод для удаления рецепта из списков."""
        recipe = get_object_or_404(Recipe, id=pk)
        deleted_count, _ = model.objects.filter(
            user=user, recipe=recipe
        ).delete()

        if deleted_count == 0:
            return Response(
                {'errors': 'Рецепта нет в этом списке!'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk):
        """Добавление рецепта в избранное или удаление из него."""
        if request.method == 'POST':
            return self.add_to_list(Favorite, request.user, pk)
        return self.remove_from_list(Favorite, request.user, pk)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        """Добавление рецепта в список покупок или удаление из него."""
        if request.method == 'POST':
            return self.add_to_list(ShoppingCart, request.user, pk)
        return self.remove_from_list(ShoppingCart, request.user, pk)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачивание списка покупок в текстовом файле."""
        user = request.user

        ingredients = (
            RecipeIngredient.objects.filter(recipe__shoppingcarts__user=user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        title = (
            f'Список покупок для: '
            f'{user.get_full_name() or user.username}\n\n'
        )
        shopping_list = [title]
        for ing in ingredients:
            shopping_list.append(
                f'- {ing["ingredient__name"]} '
                f'({ing["ingredient__measurement_unit"]}) — '
                f'{ing["total_amount"]}\n'
            )

        file_content = ''.join(shopping_list)
        response = HttpResponse(
            file_content, content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
        permission_classes=[AllowAny]
    )
    def get_link(self, request, pk):
        """Получить короткую ссылку на рецепт."""
        get_object_or_404(Recipe, id=pk)
        short_link = request.build_absolute_uri(f'/s/{pk}')
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)


class FoodgramUserViewSet(UserViewSet):
    """Вьюсет для работы с пользователями, подписками и аватарами."""

    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        """Настройка прав доступа для разных эндпоинтов."""
        if self.action in ('me', 'subscriptions', 'subscribe', 'avatar'):
            return [IsAuthenticated()]
        return [AllowAny()]

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Просмотр авторов, на которых подписан текущий пользователь."""
        user = request.user
        authors = User.objects.filter(
            following__user=user
        ).annotate(
            recipes_count_db=Count('recipes')
        ).prefetch_related(
            Prefetch('recipes', queryset=Recipe.objects.all())
        )

        page = self.paginate_queryset(authors)

        serializer = UserSubscriptionSerializer(
            page if page is not None else authors,
            many=True,
            context={'request': request}
        )

        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id):
        """Оформить подписку на автора или отменить её."""
        user = request.user
        author = get_object_or_404(User, id=id)

        if request.method == 'POST':
            if user == author:
                return Response(
                    {'errors': 'Вы не можете подписаться на самого себя!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            _, created = Follow.objects.get_or_create(
                user=user, author=author
            )
            if not created:
                return Response(
                    {'errors': 'Вы уже подписаны на этого автора!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            author.is_subscribed = True
            serializer = UserSubscriptionSerializer(
                author, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted_count, _ = Follow.objects.filter(
            user=user, author=author
        ).delete()
        if deleted_count == 0:
            return Response(
                {'errors': 'Вы не были подписаны на этого автора!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated]
    )
    def avatar(self, request):
        """Добавление, изменение или удаление аватара профиля."""
        user = request.user

        if request.method == 'PUT':
            serializer = UserAvatarSerializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        if user.avatar:
            user.avatar.delete()
        user.avatar = None
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
