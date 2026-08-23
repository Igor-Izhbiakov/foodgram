"""Управление рецептами, ингредиентами, тегами и списками пользователей."""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth import get_user_model
from django.db import models

from recipes.constants import (
    INGREDIENT_MIN_AMOUNT,
    INGREDIENT_NAME_MAX_LENGTH,
    INGREDIENT_UNIT_MAX_LENGTH,
    MAX_SMALL_INTEGER_VALUE,
    RECIPE_MIN_COOKING_TIME,
    RECIPE_NAME_MAX_LENGTH,
    TAG_NAME_MAX_LENGTH,
    TAG_SLUG_MAX_LENGTH,
)

User = get_user_model()


class Tag(models.Model):
    """Теги для классификации рецептов."""

    name = models.CharField(
        'Название тега',
        max_length=TAG_NAME_MAX_LENGTH,
        unique=True
    )
    slug = models.SlugField(
        'Уникальный слаг',
        max_length=TAG_SLUG_MAX_LENGTH,
        unique=True,
        db_index=True
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Справочник ингредиентов."""

    name = models.CharField(
        'Название ингредиента',
        max_length=INGREDIENT_NAME_MAX_LENGTH,
        db_index=True
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=INGREDIENT_UNIT_MAX_LENGTH
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient_unit'
            )
        ]

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    """Кулинарные рецепты пользователей."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор публикации'
    )
    name = models.CharField(
        'Название',
        max_length=RECIPE_NAME_MAX_LENGTH,
        db_index=True
    )
    image = models.ImageField('Картинка', upload_to='recipes/images/')
    text = models.TextField('Текстовое описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Список ингредиентов'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (в минутах)',
        validators=[
            MinValueValidator(
                RECIPE_MIN_COOKING_TIME,
                message=(
                    f'Время приготовления должно быть'
                    f'не менее {RECIPE_MIN_COOKING_TIME} минуты!'
                )
            ),
            MaxValueValidator(
                MAX_SMALL_INTEGER_VALUE,
                message=(
                    f'Время приготовления не может '
                    f'превышать {MAX_SMALL_INTEGER_VALUE} мин.!'
                )
            )
        ]
    )
    pub_date = models.DateTimeField(
        'Дата публикации', auto_now_add=True, db_index=True
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Количество конкретного ингредиента в рецепте."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT,
        related_name='ingredient_recipes',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[
            MinValueValidator(
                INGREDIENT_MIN_AMOUNT,
                message=(
                    f'Количество должно быть '
                    f'не менее {INGREDIENT_MIN_AMOUNT}!'
                )
            ),
            MaxValueValidator(
                MAX_SMALL_INTEGER_VALUE,
                message=(
                    f'Количество не может '
                    f'превышать {MAX_SMALL_INTEGER_VALUE}!'
                )
            )
        ]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.ingredient.name} — {self.amount}'


class BaseUserRecipeModel(models.Model):
    """Абстрактная базовая модель для связей Пользователь-Рецепт."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_%(class)s_recipe'
            )
        ]


class Favorite(BaseUserRecipeModel):
    """Избранные рецепты пользователей."""

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'


class ShoppingCart(BaseUserRecipeModel):
    """Рецепты в персональном списке покупок."""

    class Meta:
        verbose_name = 'Рецепт в списке покупок'
        verbose_name_plural = 'Рецепты в списке покупок'
