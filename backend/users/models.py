"""Управление пользователями и подписками."""

from django.contrib.auth.models import AbstractUser
from django.db import models

from users.constants import (
    USER_EMAIL_MAX_LENGTH,
    USER_FIRST_NAME_MAX_LENGTH,
    USER_LAST_NAME_MAX_LENGTH,
)


class User(AbstractUser):
    """Кастомная модель пользователя с авторизацией по email."""
    email = models.EmailField(
        'Адрес электронной почты',
        max_length=USER_EMAIL_MAX_LENGTH,
        unique=True,
        db_index=True
    )
    first_name = models.CharField(
        'Имя',
        max_length=USER_FIRST_NAME_MAX_LENGTH
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=USER_LAST_NAME_MAX_LENGTH
    )
    avatar = models.ImageField(
        'Аватар',
        upload_to='users/avatars/',
        blank=True,
        null=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ['username']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Follow(models.Model):
    """Система подписок на авторов рецептов."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_user_author'
            ),
            models.CheckConstraint(
                condition=~models.Q(user=models.F('author')),
                name='prevent_self_follow'
            )
        ]

    def __str__(self):
        return f'{self.user.username} подписан на {self.author.username}'
