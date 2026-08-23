"""Валидаторы для проверки входящих данных в API."""

from rest_framework import serializers


class RecipeFieldsValidator:
    """Валидатор рецепта, делегирующий проверки частям."""

    requires_context = True

    def __call__(self, attrs, serializer):
        initial_data = serializer.initial_data
        self._validate_base_structure(initial_data)
        self._validate_ingredients(initial_data.get('ingredients'))
        self._validate_tags(initial_data.get('tags'))

    def _validate_base_structure(self, initial_data):
        """Проверка пустой картинки и наличия полей при PUT/PATCH."""
        if 'image' in initial_data and not initial_data['image']:
            raise serializers.ValidationError(
                {'image': 'Поле image не может быть пустым!'}
            )
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
            if tag in tags_list:
                raise serializers.ValidationError(
                    {'tags': 'Теги в рецепте не должны дублироваться!'}
                )
            tags_list.append(tag)
