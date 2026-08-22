from django.db.models import Count, Prefetch, Sum
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
    CustomUserSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeShortSerializer,
    RecipeWriteSerializer,
    TagSerializer,
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Follow, User


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
        """Возвращает кверисет в зависимости от действия."""
        if self.action in ('list', 'retrieve'):
            return Recipe.objects.select_related('author').prefetch_related(
                'tags', 'recipe_ingredients__ingredient'
            )
        return Recipe.objects.all()

    def get_serializer_class(self):
        """Выбирает сериализатор для чтения или записи."""
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def add_to_list(self, model, user, pk):
        """Вспомогательный метод для добавления рецепта в списки."""
        if not Recipe.objects.filter(id=pk).exists():
            return Response(
                {'errors': 'Рецепт не найден.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if model.objects.filter(user=user, recipe_id=pk).exists():
            return Response(
                {'errors': 'Рецепт уже добавлен в этот список!'},
                status=status.HTTP_400_BAD_REQUEST
            )

        model.objects.create(user=user, recipe_id=pk)

        recipe = Recipe.objects.get(id=pk)
        serializer = RecipeShortSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def remove_from_list(self, model, user, pk):
        """Вспомогательный метод для удаления рецепта из списков."""
        if not Recipe.objects.filter(id=pk).exists():
            return Response(
                {'errors': 'Рецепт не найден.'},
                status=status.HTTP_404_NOT_FOUND
            )

        obj = model.objects.filter(user=user, recipe_id=pk)
        if not obj.exists():
            return Response(
                {'errors': 'Рецепта нет в этом списке!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        obj.delete()
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
        """АСкачивание списка покупок в текстовом файле."""
        user = request.user
        if not ShoppingCart.objects.filter(user=user).exists():
            return Response(
                {'errors': 'Ваш список покупок пуст!'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ingredients = (
            RecipeIngredient.objects.filter(recipe__shopping_carts__user=user)
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
        if not Recipe.objects.filter(id=pk).exists():
            return Response(
                {'errors': 'Рецепт не найден.'},
                status=status.HTTP_404_NOT_FOUND
            )
        short_link = request.build_absolute_uri(f'/s/{pk}')
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)


class CustomUserViewSet(UserViewSet):
    """Вьюсет для работы с пользователями, подписками и аватарами."""

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer

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

        results = []
        for author in (page if page is not None else authors):
            author_data = self.get_serializer(author).data
            recipes = author.recipes.all()

            recipes_limit = request.query_params.get('recipes_limit')
            if recipes_limit and recipes_limit.isdigit():
                recipes = recipes[:int(recipes_limit)]

            author_data['recipes'] = RecipeShortSerializer(
                recipes,
                many=True,
                context={'request': request}
            ).data
            author_data['recipes_count'] = author.recipes.count()
            results.append(author_data)

        if page is not None:
            return self.get_paginated_response(results)
        return Response(results, status=status.HTTP_200_OK)

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
            if Follow.objects.filter(user=user, author=author).exists():
                return Response(
                    {'errors': 'Вы уже подписаны на этого автора!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Follow.objects.create(user=user, author=author)

            author_data = self.get_serializer(author).data
            recipes = author.recipes.all()
            recipes_limit = request.query_params.get('recipes_limit')
            if recipes_limit and recipes_limit.isdigit():
                recipes = recipes[:int(recipes_limit)]
            author_data['recipes'] = RecipeShortSerializer(
                recipes,
                many=True,
                context={'request': request}
            ).data
            author_data['recipes_count'] = author.recipes.count()
            return Response(author_data, status=status.HTTP_201_CREATED)

        follow = Follow.objects.filter(user=user, author=author)
        if not follow.exists():
            return Response(
                {'errors': 'Вы не были подписаны на этого автора!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        follow.delete()
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
            if 'avatar' not in request.data:
                return Response(
                    {'avatar': 'Это поле обязательно для заполнения!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = self.get_serializer(
                user, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {'avatar': user.avatar.url}, status=status.HTTP_200_OK
            )

        if user.avatar:
            user.avatar.delete()
        user.avatar = None
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
