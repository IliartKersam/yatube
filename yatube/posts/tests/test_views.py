import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Post, Group, Comment, Follow
from ..forms import CommentForm

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user_1 = User.objects.create_user(username='auth')
        cls.user_2 = User.objects.create_user(username='auth_2')
        cls.group_1 = Group.objects.create(title='Тестовая группа №1',
                                           slug='test_slug',
                                           description='Тестовое описание')
        cls.group_2 = Group.objects.create(title='Тестовая группа №2',
                                           slug='test_slug_2',
                                           description='Тестовое описание_2')
        cls.post_1 = Post.objects.create(author=cls.user_1,
                                         text='Самый лучший пост',
                                         group_id=cls.group_1.id,
                                         image=uploaded)
        cls.comment_1 = Comment.objects.create(
            author=cls.user_1,
            text='Комментарий к посту 1',
            post_id=cls.post_1.id
        )
        cls.index_url = ('posts:index', 'posts/index.html', '')
        cls.post_create_url = (
            'posts:post_create', 'posts/create_post.html', ''
        )
        cls.group_1_url = (
            'posts:group_list', 'posts/group_list.html', (cls.group_1.slug,)
        )
        cls.group_2_url = (
            'posts:group_list', 'posts/group_list.html', (cls.group_2.slug,)
        )
        cls.profile_1_url = (
            'posts:profile', 'posts/profile.html', (cls.user_1.username,)
        )
        cls.profile_2_url = (
            'posts:profile', 'posts/profile.html', (cls.user_2.username,)
        )
        cls.post_detail_url = (
            'posts:post_detail', 'posts/post_detail.html', (cls.post_1.id,)
        )
        cls.post_edit_url = (
            'posts:post_edit', 'posts/create_post.html', (cls.post_1.id,)
        )
        cls.profile_follow_url = (
            'posts:profile_follow', 'posts/profile.html', (
                (cls.user_1.username,)
            )
        )
        cls.profile_unfollow_url = (
            'posts:profile_unfollow', 'posts/profile.html', (
                (cls.user_1.username,)
            )
        )
        cls.follow_url = ('posts:follow_index', 'posts/follow.html', '')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client_2 = Client()
        self.authorized_client.force_login(PostsPagesTests.user_1)
        self.authorized_client_2.force_login(PostsPagesTests.user_2)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        urls = (
            PostsPagesTests.index_url,
            PostsPagesTests.post_create_url,
            PostsPagesTests.group_1_url,
            PostsPagesTests.profile_1_url,
            PostsPagesTests.post_detail_url,
            PostsPagesTests.post_edit_url,
        )

        for url, template, args in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(reverse(url, args=args))
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_index_context(self):
        """Проверяем, что на главную страницу передается список постов."""
        url, _, _ = PostsPagesTests.index_url
        response = self.authorized_client.get(reverse(url))
        self.assertIn('page_obj', response.context)
        page_objects = response.context['page_obj'][0]
        self.assertIsInstance(page_objects, Post)

    def test_filter_context_group_list(self):
        """Тест того что на страницу группы передаются записи
        определенной группы."""
        url, _, args = PostsPagesTests.group_1_url
        response = self.authorized_client.get(reverse(url, args=args))
        objects = response.context['page_obj'][0]
        attributes = {
            objects.group.id: PostsPagesTests.group_1.id,
            objects.group.title: PostsPagesTests.group_1.title,
            objects.group.slug: PostsPagesTests.group_1.slug,
            objects.group.description: PostsPagesTests.group_1.description
        }
        for attribute, group_attribute in attributes.items():
            with self.subTest(attribute=attribute):
                self.assertEqual(attribute, group_attribute)
        self.assertIsInstance(objects, Post)

    def test_filter_context_profile(self):
        """Тест того что на страницу профайла передаются записи
        определенного автора."""
        url, _, args = PostsPagesTests.profile_1_url
        response = self.authorized_client.get(reverse(url, args=args))
        objects = response.context['page_obj'][0]
        self.assertEqual(objects.author.username,
                         PostsPagesTests.user_1.username)
        self.assertIsInstance(objects, Post)

    def test_paginator_at_all_pages(self):
        """Тестируем работу пагинатора на всех страницах."""
        new_posts_count = 12
        objs = [
            Post(
                author=PostsPagesTests.user_1,
                text=f'Этот пост добавлен в цикле, его номер - {num}',
                group_id=PostsPagesTests.group_1.id
            )
            for num in range(new_posts_count)
        ]
        Post.objects.bulk_create(objs=objs)
        urls = (
            PostsPagesTests.index_url,
            PostsPagesTests.group_1_url,
            PostsPagesTests.profile_1_url
        )
        first_page_amount = 10
        second_page_amount = 3
        post_at_page = ((1, first_page_amount), (2, second_page_amount))
        for url, _, args in urls:
            for page, count in post_at_page:
                with self.subTest(url=url):
                    response = self.authorized_client.get(
                        reverse(url, args=args), {'page': page}
                    )
                    self.assertEqual(
                        len(response.context['page_obj']), count
                    )

    def test_filter_context_post_detail(self):
        """Тест того что на страницу детализации поста передается
        1 нужный пост."""
        url, _, args = PostsPagesTests.post_detail_url
        response = self.authorized_client.get(reverse(url, args=args))
        objects = response.context['post']
        attributes = {
            objects.id: PostsPagesTests.post_1.id,
            objects.text: PostsPagesTests.post_1.text,
            objects.group.id: PostsPagesTests.post_1.group.id,
            objects.group.slug: PostsPagesTests.group_1.slug,
            objects.author.username: PostsPagesTests.post_1.author.username,
        }
        for attribute, post_attribute in attributes.items():
            with self.subTest(attribute=attribute):
                self.assertEqual(attribute, post_attribute)

    def test_new_post_in_index(self):
        """Проверяем, что созданный пост отображается на главной странице."""
        url, _, _ = PostsPagesTests.index_url
        response = self.authorized_client.get(reverse(url))
        posts = response.context.get('page_obj').object_list
        self.assertIn(PostsPagesTests.post_1, posts)

    def test_new_post_in_correct_group_list(self):
        """Проверяем, что созданный пост отображается на странице
        своей группы."""
        url, _, args = PostsPagesTests.group_1_url
        response = self.authorized_client.get(reverse(url, args=args))
        posts = response.context.get('page_obj').object_list
        self.assertIn(PostsPagesTests.post_1, posts)

    def test_post_didnt_belong_in_another_group(self):
        """Тест того что в группу 2 не попал пост, который
        относится к группе 1."""
        url, _, args = PostsPagesTests.group_2_url
        response = self.authorized_client.get(reverse(url, args=args))
        posts = response.context.get('page_obj').object_list
        self.assertNotIn(PostsPagesTests.post_1, posts)

    def test_form_new_post_context(self):
        """Проверяем, что в контекст создания новой формы и формы
        редактирования переданы соответствующие поля."""
        urls = (
            PostsPagesTests.post_create_url,
            PostsPagesTests.post_edit_url
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for url, _, args in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(reverse(url, args=args))
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get('form').fields.get(
                            value)
                        self.assertIsInstance(form_field, expected)

    def test_form_edit_correct_post(self):
        """Проверяем, что в форму для редактирования передается нужный пост."""
        url, _, args = PostsPagesTests.post_edit_url
        response = self.authorized_client.get(
            reverse(url, args=args))
        post_to_edit = response.context['form']
        self.assertEqual(post_to_edit.instance.id, PostsPagesTests.post_1.id)

    def test_image_in_context(self):
        """Проверяем, что картинка в посте попала в контекст нужных страниц."""
        urls = (
            PostsPagesTests.index_url,
            PostsPagesTests.group_1_url,
            PostsPagesTests.profile_1_url,
            PostsPagesTests.post_detail_url,
        )
        for url, _, args in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(reverse(url, args=args))
                if url != 'posts:post_detail':
                    objects = response.context['page_obj'][0]
                else:
                    objects = response.context['post']
                self.assertEqual(PostsPagesTests.post_1.image, objects.image)

    def test_new_comment_in_post_detail(self):
        """Проверяем, что новый комментарий попал на страницу поста."""
        url, _, args = PostsPagesTests.post_detail_url
        response = self.authorized_client.get(reverse(url, args=args))
        comments = response.context['comments']
        self.assertIn(PostsPagesTests.comment_1, comments)

    def test_ceche_in_index(self):
        """Проверяем работу кеша на странице index."""
        url, _, _ = PostsPagesTests.index_url
        response_1 = self.authorized_client.get(reverse(url))
        Post.objects.filter(pk=1).delete()
        response_2 = self.authorized_client.get(reverse(url))
        self.assertEqual(response_1.content, response_2.content)
        cache.clear()
        response_3 = self.authorized_client.get(reverse(url))
        self.assertNotEqual(response_1.content, response_3.content)

    def test_authorized_client_can_be_follower(self):
        """Авторизованный пользователь может подписываться на других
        пользователей и удалять их из подписок."""
        follow_count_1 = Follow.objects.count()
        url, _, args = PostsPagesTests.profile_follow_url
        self.authorized_client_2.get(reverse(url, args=args))
        follow_count_2 = Follow.objects.count()
        self.assertEqual(follow_count_2, follow_count_1 + 1)
        url, _, args = PostsPagesTests.profile_unfollow_url
        self.authorized_client_2.get(reverse(url, args=args))
        follow_count_3 = Follow.objects.count()
        self.assertEqual(follow_count_1, follow_count_3)

    def test_following_post_in_follower_branch(self):
        """Новая запись пользователя появляется в ленте тех, кто на него
        подписан и не появляется в ленте тех, кто не подписан."""
        Follow.objects.create(user=PostsPagesTests.user_2,
                              author=PostsPagesTests.user_1)
        url, _, _ = PostsPagesTests.follow_url
        response = self.authorized_client_2.get(reverse(url))
        posts = response.context.get('page_obj').object_list
        self.assertIn(PostsPagesTests.post_1, posts)
        response = self.authorized_client.get(reverse(url))
        posts = response.context.get('page_obj').object_list
        self.assertNotIn(PostsPagesTests.post_1, posts)
