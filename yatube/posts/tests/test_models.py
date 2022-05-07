from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils.text import Truncator

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст тестового поста, который должен быть обрезан',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__. У Post текс т
        обрезается жо 30 символов, у Group выводится наименование группы."""
        post_str = Truncator(str(PostModelTest.post)).chars(30)
        group_str = 'Тестовая группа'
        self.assertEqual(str(PostModelTest.group), group_str)
        self.assertEqual(str(PostModelTest.post), post_str)

    def test_post_verbose_names(self):
        """Проверяем, что verbose_name полей модели
        Post совпадает с ожидаемым."""
        vb_names = {
            'text': 'Текст поста',
            'pub_date': 'Дата создания',
            'author': 'Автор',
            'group': 'Группа'
        }
        for field, vb_name in vb_names.items():
            with self.subTest(field=field):
                verbose = PostModelTest.post._meta.get_field(
                    field).verbose_name
                self.assertEqual(verbose, vb_name)

    def test_title_help_text(self):
        """Проверяем, что help_text полей модели
        Post совпадает с ожидаемым."""
        hp_texts = {
            'text': 'Введите текст поста',
            'group': 'Вы можете выбрать группу для вашего поста.'
        }
        for field, hp_text in hp_texts.items():
            with self.subTest(field=field):
                help_text = PostModelTest.post._meta.get_field(field).help_text
                self.assertEqual(help_text, hp_text)
