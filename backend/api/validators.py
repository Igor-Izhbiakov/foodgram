"""Валидаторы для проверки входящих данных в API."""

from rest_framework import serializers
from recipes.models import Ingredient


class RecipeFieldsValidator:
    """Монолитный валидатор рецепта, делегирующий проверки частям."""

    requires_context = True

    def __call__(self, attrs, serializer):
        initial_data = serializer.initial_data
        request = serializer.context.get('request')
        self._validate_base_structure(initial_data, request)
        self._validate_ingredients(initial_data.get('ingredients'))
        self._validate_tags(initial_data.get('tags'))

    def _validate_base_structure(self, initial_data, request):
        """Проверка пустой картинки и наличия полей при PUT/PATCH."""
        if 'image' in initial_data and not initial_data['image']:
            raise serializers.ValidationError(
                {'image': 'Поле image не может быть пустым!'}
            )
        if request and request.method in ('PUT', 'PATCH'):
            if 'ingredients' not in initial_data:
                raise serializers.ValidationError(
                    {'ingredients': 'Это поле обязательно для заполнения.'}
                )
            if 'tags' not in initial_data:
                raise serializers.ValidationError(
                    {'tags': 'Это поле обязательно для заполнения.'}
                )

    def _validate_ingredients(self, ingredients):
        """Изолированная валидация списка ингредиентов."""
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Необходимо выбрать хотя бы один ингредиент!'}
            )
        if not isinstance(ingredients, list):
            raise serializers.ValidationError(
                {'ingredients': 'Ингредиенты должны быть списком!'}
            )

        ingredients_list = []
        for item in ingredients:
            if not isinstance(item, dict):
                raise serializers.ValidationError(
                    {'ingredients': 'Некорректный формат ингредиента!'}
                )

            ingredient_id = item.get('id')
            amount = item.get('amount')

            if ingredient_id is None or (
                not isinstance(ingredient_id, int)
                and not (
                    isinstance(ingredient_id, str)
                    and ingredient_id.isdigit()
                )
            ):
                raise serializers.ValidationError(
                    {
                        'ingredients': (
                            f'Некорректный ID ингредиента: '
                            f'{ingredient_id}'
                        )
                    }
                )

            ingredient_id = int(ingredient_id)

            if not Ingredient.objects.filter(id=ingredient_id).exists():
                raise serializers.ValidationError(
                    {
                        'ingredients': (
                            f'Ингредиент с id '
                            f'{ingredient_id} не существует!'
                        )
                    }
                )

            if ingredient_id in ingredients_list:
                raise serializers.ValidationError(
                    {
                        'ingredients': (
                            'Ингредиенты в рецепте '
                            'не должны дублироваться!'
                        )
                    }
                )
            ingredients_list.append(ingredient_id)

            if amount is None:
                raise serializers.ValidationError(
                    {
                        'ingredients': (
                            'Количество ингредиента '
                            'должно быть указано!'
                        )
                    }
                )
            try:
                if int(amount) < 1:
                    raise serializers.ValidationError(
                        {
                            'ingredients': (
                                'Количество ингредиента '
                                'должно быть больше 0!'
                            )
                        }
                    )
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    {
                        'ingredients': (
                            'Количество ингредиента '
                            'должно быть числом!'
                        )
                    }
                )

    def _validate_tags(self, tags):
        """Изолированная валидация списка тегов."""
        if not tags:
            raise serializers.ValidationError(
                {'tags': 'Необходимо выбрать хотя бы один тег!'}
            )
        if not isinstance(tags, list):
            raise serializers.ValidationError(
                {'tags': 'Теги должны быть списком!'}
            )

        tags_list = []
        for tag in tags:
            tag_id = tag.get('id') if isinstance(tag, dict) else tag
            if tag_id is None or (
                not isinstance(tag_id, int)
                and not (isinstance(tag_id, str) and tag_id.isdigit())
            ):
                raise serializers.ValidationError(
                    {'tags': f'Некорректный ID тега: {tag_id}'}
                )

            tag_id = int(tag_id)

            if tag_id in tags_list:
                raise serializers.ValidationError(
                    {'tags': 'Теги в рецепте не должны дублироваться!'}
                )
            tags_list.append(tag_id)
