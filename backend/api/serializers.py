"""Сериализаторы для работы с API проекта Фудграм."""

from django.contrib.auth import get_user_model
from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from api.validators import (
    RecipeFieldsValidator,
)
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import Follow

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
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
        if hasattr(obj, 'is_subscribed'):
            return obj.is_subscribed
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and Follow.objects.filter(user=request.user, author=obj).exists()
        )


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


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с ингредиентами в рецепте (чтение и запись)."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецептов (GET-запросы)."""

    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True
    )
    is_favorited = serializers.BooleanField(read_only=True, default=False)
    is_in_shopping_cart = serializers.BooleanField(
        read_only=True,
        default=False
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов (POST/PATCH)."""

    ingredients = RecipeIngredientSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    image = Base64ImageField(
        required=True,
        allow_null=False,
        allow_empty_file=False
    )

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image', 'name',
            'text', 'cooking_time'
        )
        validators = [RecipeFieldsValidator()]

    def create_ingredients_amounts(self, ingredients, recipe):
        """Доп метод для записи ингредиентов в связующую таблицу."""
        RecipeIngredient.objects.bulk_create(
            [
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=ing.get('ingredient'),
                    amount=ing.get('amount')
                )
                for ing in ingredients
            ]
        )

    @transaction.atomic
    def create(self, validated_data):
        """Создание рецепта с сохранением тегов и ингредиентов."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        recipe = Recipe.objects.create(
            author=self.context['request'].user, **validated_data
        )
        recipe.tags.set(tags)
        self.create_ingredients_amounts(ingredients, recipe)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Обновление рецепта с предварительной очисткой старых связей."""
        ingredients = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)

        instance = super().update(instance, validated_data)
        if tags is not None:
            instance.tags.set(tags)

        if ingredients is not None:
            instance.recipe_ingredients.all().delete()
            self.create_ingredients_amounts(ingredients, instance)

        return instance

    def to_representation(self, instance):
        """После создания/обновления возвращает рецепт в развернутом виде."""
        return RecipeReadSerializer(instance, context=self.context).data


class RecipeShortSerializer(serializers.ModelSerializer):
    """Компактный сериализатор рецепта для показа в покупах и подписках."""

    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def get_image(self, obj):
        """Возвращает абсолютную ссылку на картинку в виде строки."""
        if obj.image:
            return obj.image.url
        return ""


class UserSubscriptionSerializer(UserSerializer):
    """Сериализатор для вывода авторов, на которых оформлена подписка."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        """Возвращает список рецептов автора с учетом лимита."""
        request = self.context.get('request')
        recipes = list(obj.recipes.all())
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit and recipes_limit.isdigit():
            recipes = recipes[:int(recipes_limit)]
        return RecipeShortSerializer(
            recipes,
            many=True,
            context={'request': request}
        ).data

    def get_recipes_count(self, obj):
        """Возвращает количество рецептов автора."""
        if hasattr(obj, 'recipes_count_db'):
            return obj.recipes_count_db
        return obj.recipes.count()


class UserAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для валидации и обновления аватарки профиля."""

    avatar = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = User
        fields = ('avatar',)
