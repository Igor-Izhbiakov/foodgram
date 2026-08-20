"""Сериализаторы для работы с API проекта Фудграм."""

from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from rest_framework import serializers

from api.validators import validate_ingredients_list, validate_tags_list
from users.models import Follow

User = get_user_model()


class CustomUserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации новых пользователей."""

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'password'
        )
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        """Хеширует пароль перед сохранением пользователя в базу."""
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class CustomUserSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения профилей пользователей."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на данного автора."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Follow.objects.filter(user=request.user, author=obj).exists()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения ингредиентов внутри рецепта."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецептов (GET-запросы)."""

    author = CustomUserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        """Проверяет, добавлен ли рецепт в избранное."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.favorites.filter(user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, добавлен ли рецепт в список покупок."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.shopping_carts.filter(user=request.user).exists()


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для записи ингредиентов при создании рецепта."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов (POST/PATCH)."""

    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientWriteSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image', 'name',
            'text', 'cooking_time', 'author'
        )

    def validate_ingredients(self, value):
        """Запуск внешнего валидатора для проверки ингредиентов."""
        return validate_ingredients_list(value)

    def validate_tags(self, value):
        """Запуск внешнего валидатора для проверки тегов."""
        return validate_tags_list(value)

    def create_ingredients_amounts(self, ingredients, recipe):
        """Доп метод для записи ингредиентов в связующую таблицу."""
        RecipeIngredient.objects.bulk_create(
            [RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient.get('id'),
                amount=ingredient.get('amount')
            ) for ingredient in ingredients]
        )

    def create(self, validated_data):
        """Создание рецепта с ручным сохранением тегов и ингредиентов."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        recipe = Recipe.objects.create(
            author=self.context['request'].user, **validated_data
        )
        recipe.tags.set(tags)
        self.create_ingredients_amounts(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Обновление рецепта с предварительной очисткой старых связей."""
        ingredients = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)

        instance = super().update(instance, validated_data)

        if tags is not None:
            instance.tags.set(tags)

        if ingredients is not None:
            RecipeIngredient.objects.filter(recipe=instance).delete()
            self.create_ingredients_amounts(ingredients, instance)

        return instance

    def to_representation(self, instance):
        """После создания/обновления возвращает рецепт в развернутом виде."""
        return RecipeReadSerializer(instance, context=self.context).data


class RecipeShortSerializer(serializers.ModelSerializer):
    """Компактный сериализатор рецепта для показа в покупах и подписках."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
