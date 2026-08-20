"""Управление рецептами, ингредиентами, тегами и списками пользователей."""

from django.core.validators import MinValueValidator
from django.db import models
from users.models import User


class Tag(models.Model):
    """Теги для классификации рецептов."""

    name = models.CharField('Название тега', max_length=200, unique=True)
    slug = models.SlugField(
        'Уникальный слаг', max_length=200, unique=True, db_index=True
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
        'Название ингредиента', max_length=200, db_index=True
    )
    measurement_unit = models.CharField('Единица измерения', max_length=200)

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
    name = models.CharField('Название', max_length=200, db_index=True)
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
                1, message='Время приготовления должно быть не менее 1 минуты!'
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
        validators=[MinValueValidator(
            1, message='Количество должно быть не менее 1!'
        )]
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


class Favorite(models.Model):
    """Избранные рецепты пользователей."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_favorite_recipe'
            )
        ]


class ShoppingCart(models.Model):
    """Рецепты в персональном списке покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_carts',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_carts',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Рецепт в списке покупок'
        verbose_name_plural = 'Рецепты в списке покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_shopping_cart_recipe'
            )
        ]
