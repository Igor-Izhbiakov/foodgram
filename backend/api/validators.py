"""Валидаторы для проверки входящих данных в API."""

from rest_framework import serializers


def validate_ingredients_list(value):
    """Проверяет список ингредиентов на пустоту, дубликаты и количество."""
    if not value:
        raise serializers.ValidationError(
            'Необходимо выбрать хотя бы один ингредиент!'
        )

    ingredients_list = []
    for item in value:
        ingredient_id = item.get('id')

        if ingredient_id in ingredients_list:
            raise serializers.ValidationError(
                'Ингредиенты в рецепте не должны дублироваться!'
            )
        ingredients_list.append(ingredient_id)

        amount = item.get('amount')
        if amount is None or int(amount) < 1:
            raise serializers.ValidationError(
                'Количество ингредиента должно быть больше 0!'
            )

    return value


def validate_tags_list(value):
    """Проверяет список тегов на пустоту и уникальность."""
    if not value:
        raise serializers.ValidationError(
            'Необходимо выбрать хотя бы один тег!'
        )

    tags_list = []
    for tag in value:
        tag_id = getattr(
            tag,
            'id',
            tag if not isinstance(tag, dict) else tag.get('id')
        )

        if tag_id in tags_list:
            raise serializers.ValidationError(
                'Теги в рецепте не должны дублироваться!'
            )
        tags_list.append(tag_id)

    return value
