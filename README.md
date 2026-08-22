# Проект Foodgram

## Описание
«Фудграм» — сайт, на котором пользователи публикуют свои рецепты, добавляют чужие рецепты в избранное и подписываются на публикации других авторов. Зарегистрированным пользователям доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

## Технологии и библиотеки
* **Язык программирования:** Python 3.12
* **Основные библиотеки:**
  * Django
  * Django REST Framework
  * Django-filter
  * Django-placeholder-field / drf-extra-fields:
  * Djoser
  * Docker, Docker Compose
  * Flake8
  * Nginx
  * Pillow
  * PostgreSQL (Production)
  * Postman
  * Pytest / Pytest-django
  * SQLite

## Документация API
После запуска проекта подробное описание всех эндпоинтов и примеров запросов доступно по ссылке:
* **Redoc:** [http://localhost/api/docs/](http://localhost/api/docs/)

## Установка и запуск проекта

1. Клонируйте репозиторий:
   ```bash
   git clone git@github.com:Igor-Izhbiakov/foodgram
   ```

2. Перейдите в папку проекта:
    ```bash
    cd foodgram
    ```

3. Cоздайте и активируйте виртуальное окружение:
   * Для Windows:
     ```bash
     python -m venv venv
     source venv/Scripts/activate
     ```
   * Для macOS / Linux:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

4. Установите зависимости из файла requirements.txt:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. Выполните миграции для создания структуры базы данных:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. Наполните базу данных начальными данными из CSV-файлов:
   ```bash
   python manage.py load_ingredients
   ```

7. Запустите сервер разработки:
   ```bash
   python manage.py runserver
   ```

Проект будет доступен по адресу: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)  
Документация ReDoc подключена по адресу: [http://localhost/api/docs/](http://localhost/api/docs/)

## Алгоритм регистрации и аутентификации пользователей

В проекте используется Token-аутентификация на базе библиотеки **Djoser**:

1. **Регистрация пользователя**: Пользователь отправляет `POST`-запрос со своими данными (`email`, `username`, `first_name`, `last_name`, `password`) на эндпоинт `/api/users/`.
2. **Получение токена**: Пользователь отправляет `POST`-запрос с параметрами `email` и `password` на эндпоинт `/api/auth/token/login/`. В ответе возвращается авторизационный токен (`auth_token`).
3. **Авторизация запросов**: При каждом следующем запросе к защищенным эндпоинтам токен передается в заголовке `Authorization` в формате:
   ```http
   Authorization: Token <значение_токена>
   ```
4. **Выход из системы**: Для удаления токена отправляется `POST`-запрос на эндпоинт `/api/auth/token/logout/`.

## Пользовательские роли и права доступа

* **Анонимный пользователь** — может просматривать список рецептов, отдельные рецепты, список ингредиентов и тегов. Доступно получение коротких ссылок на рецепты.
* **Аутентифицированный пользователь** — обладает всеми правами анонима, а также может:
  * Создавать, редактировать и удалять *свои* рецепты.
  * Добавлять рецепты в «Избранное» и «Список покупок», скачивать сводный файл продуктов.
  * Подписываться на других авторов и просматривать свою ленту подписок.
* **Администратор / Суперпользователь Django** — обладает полными правами на управление всем контентом и пользователями проекта через панель администратора.

## Примеры запросов к API

### Получение списка рецептов
* **Запрос**: `GET /api/recipes/` (Доступно всем, поддерживает фильтрацию и пагинацию)
* **Ответ (`200 OK`)**:
  ```json
  {
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 1,
        "tags": [
          {
            "id": 1,
            "name": "Завтрак",
            "slug": "breakfast"
          }
        ],
        "author": {
          "email": "ivanov@yandex.ru",
          "id": 2,
          "username": "vasya.ivanov",
          "first_name": "Вася",
          "last_name": "Иванов",
          "is_subscribed": false,
          "avatar": null
        },
        "ingredients": [
          {
            "id": 170,
            "name": "Буррата",
            "measurement_unit": "г",
            "amount": 100
          }
        ],
        "is_favorited": false,
        "is_in_shopping_cart": false,
        "name": "Тост с бурратой",
        "image": "http://127.0.0",
        "text": "Выложите буррату на поджаренный тост.",
        "cooking_time": 5
      }
    ]
  }
  ```

### Добавление нового рецепта (Только для авторизованных)
* **Запрос**: `POST /api/recipes/`
* **Тело запроса**:
  ```json
  {
    "ingredients": [
      {
        "id": 170,
        "amount": 100
      }
    ],
    "tags":,
    "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg==",
    "name": "Быстрый тост",
    "text": "Приготовить любым способом",
    "cooking_time": 5
  }
  ```
* **Ответ (`201 Created`)**: Возвращает полную структуру созданного рецепта.

### Подписка на автора (Только для авторизованных)
* **Запрос**: `POST /api/users/{user_id}/subscribe/?recipes_limit=2`
* **Ответ (`201 Created`)**:
  ```json
  {
    "email": "author@email.org",
    "id": 3,
    "username": "chef",
    "first_name": "Андрей",
    "last_name": "Иванов",
    "is_subscribed": true,
    "avatar": null,
    "recipes": [
      {
        "id": 4,
        "name": "Нечто жареное",
        "image": "http://127.0.0",
        "cooking_time": 10
      }
    ],
    "recipes_count": 1
  }
  ```

## Развертывание проекта на удаленном сервере (Production)

### Архитектура сети на сервере
На удаленном сервере реализована многопроектная архитектура изолированных контейнеров:
1. **Внешний (глобальный) Nginx:** Запущен напрямую на хост-машине. Он слушает входящий HTTP-трафик из внешнего мира (порты `80` и `443`), определяет доменные имена сайтов и перенаправляет (проксирует) запросы на порты соответствующих внутренних контейнеров.
2. **Изолированный стек проекта Foodgram:** Управляется через Docker Compose и включает в себя:
   - Внутренний контейнер веб-сервера **Nginx (foodgram-proxy)**, принимающий проксированный трафик от глобального сервера на выделенном порту. Он раздает статику фронтенда (`react_static`), бэкенда (`django_static`) и медиафайлы (`media_value`).
   - Контейнер бэкенда **Django (foodgram-backend)**, запущенный через WSGI-сервер Gunicorn на порту `8000`.
   - Контейнер фронтенда **React (foodgram-front)** для сборки статических файлов интерфейса.
   - Контейнер базы данных **PostgreSQL (foodgram-db)**, полностью изолированный внутри внутренней сети Docker-сети проекта.

### Инструкция по деплою проекта

1. **Подготовка папки проекта на сервере:**
   ```bash
   mkdir -p foodgram && cd foodgram
   ```

2. **Настройка переменных окружения:**
   Внутри папки `foodgram/` создайте файл `.env` (`nano .env`) и заполните его боевыми данными:
   ```env
   POSTGRES_USER=foodgram_user
   POSTGRES_PASSWORD=ваша_надежная_парольная_фраза
   POSTGRES_DB=foodgram
   DB_HOST=db
   DB_PORT=5432
   SECRET_KEY='secret_key'
   DEBUG=False
   ALLOWED_HOSTS=localhost,127.0.0.1,158.160.193.212,yourfoodgram.duckdns.org
   ```

3. **Запуск контейнеров через CI/CD:**
   Файл `docker-compose.production.yml` автоматически копируется на сервер, а сборка образов и их перезапуск происходят автоматически при каждом пуше в ветку `main` благодаря настроенному GitHub Actions Workflow.
   *(Для ручного перезапуска используется команда: `docker compose -f docker-compose.production.yml up -d --build`)*

4. **Первоначальная настройка базы данных внутри Docker:**
   При первом запуске проекта выполните по очереди команды внутри контейнера бэкенда:
   ```bash
   docker compose exec backend python manage.py migrate
   docker compose exec backend python manage.py collectstatic --no-input
   docker compose exec backend python manage.py load_ingredients
   docker compose exec backend python manage.py createsuperuser
   ```

## Авторы проекта
Разработчик бэкенда: [Igor Izhbiakov](https://github.com)