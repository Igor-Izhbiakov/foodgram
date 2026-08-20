"""Кастомная команда для импорта ингредиентов из JSON-файла."""

import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    """Загружает ингредиенты из папки data в базу данных."""

    help = 'Импортирует ингредиенты из файла ingredients.json'

    def handle(self, *args, **options):
        path = os.path.join(
            settings.BASE_DIR, '..', 'data', 'ingredients.json'
        )

        if not os.path.exists(path):
            self.stdout.write(
                self.style.ERROR(f'Файл не найден по пути: {path}')
            )
            return

        self.stdout.write('Начало импорта ингредиентов...')

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        ingredients_to_create = []
        for item in data:
            ingredients_to_create.append(
                Ingredient(
                    name=item['name'],
                    measurement_unit=item['measurement_unit']
                )
            )

        Ingredient.objects.bulk_create(
            ingredients_to_create, ignore_conflicts=True
        )

        self.stdout.write(
            self.style.SUCCESS('Ингредиенты успешно импортированы!')
        )
