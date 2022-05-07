from django.contrib.auth import get_user_model
from django.db import models
from django.utils.text import Truncator
from core.models import CreatedModel

User = get_user_model()


class Group(models.Model):
    """Создаем класс для модели группы."""

    title = models.CharField(max_length=200, verbose_name='Название группы')
    slug = models.SlugField(unique=True, verbose_name='Короткая ссылка')
    description = models.TextField(verbose_name='Описание группы')

    def __str__(self) -> str:
        """Функция для вывода на печать."""
        return self.title

    class Meta:
        verbose_name_plural = 'Сообщества'
        verbose_name = 'Сообщество'


class Post(CreatedModel):
    """Создаем класс для модели Post."""

    text = models.TextField(verbose_name='Текст поста',
                            help_text='Введите текст поста')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='posts',
        verbose_name='Группа',
        help_text='Вы можете выбрать группу для вашего поста.'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True,
        help_text='Выберете картинку для Вашего поста.'
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name_plural = 'Посты'
        verbose_name = 'Пост'

    def __str__(self) -> str:
        """Функция для вывода на печать."""
        return Truncator(self.text).chars(30)


class Comment(CreatedModel):
    """Создаем класс для модели Comment."""

    text = models.TextField('Текст комментария',
                            help_text='Напишите Ваш комментарий в это поле.')
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор'
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name_plural = 'Комментарии'
        verbose_name = 'Комментарий'

    def __str__(self) -> str:
        """Функция для вывода на печать."""
        return Truncator(self.text).chars(30)


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Пользователь'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'

    )

    class Meta:
        verbose_name_plural = 'Подписки'
        verbose_name = 'Подписка'
