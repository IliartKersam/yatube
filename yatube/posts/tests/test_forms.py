import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Post, Group, Comment

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    """В этом классе протестируем формы."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(title='Тестовая группа №1',
                                         slug='test_slug',
                                         description='Тестовое описание')
        cls.group_2 = Group.objects.create(title='Тестовая группа №2',
                                           slug='test_slug_2',
                                           description='Тестовое описание_2')
        cls.post = Post.objects.create(author=cls.user,
                                       text='Самый лучший пост',
                                       group_id=cls.group.id)
        Post.objects.create(author=cls.user,
                            text='Самый лучший пост_2',
                            group_id=cls.group.id)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)

    def test_authorized_client_can_create_post(self):
        """Проверяем, что авторизованный пользователь может
        создать новый пост."""
        new_post_count = 1
        post_count = Post.objects.count()
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
        form_data = {
            'text': 'Текст из формы',
            'group': PostFormTests.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count + new_post_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response,
                             f'/profile/{PostFormTests.user.username}/')
        self.assertTrue(
            Post.objects.filter(
                text='Текст из формы',
                group_id=PostFormTests.group.id,
                image='posts/small.gif'
            ).exists()
        )

    def test_guest_client_cant_create_post(self):
        """Проверяем, что не аторизованный пользователь не может создать
         новый пост."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Текст из формы',
            'group_id': PostFormTests.group.id,
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_can_edit_post(self):
        """Проверяем, что редактирование поста не приводит к добавлению
        нового поста, в отредактированном посте появились новые данные, и для
        редактирования передается нужный пост"""
        post_count = Post.objects.count()
        group_post_count = PostFormTests.group.posts.count()
        posts_changed_group = 1
        form_data = {
            'text': 'Текст из формы',
            'group_id': PostFormTests.group_2.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostFormTests.post.id}),
            data=form_data, follow=True)
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(
            PostFormTests.group.posts.count(),
            group_post_count - posts_changed_group
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, f'/posts/{PostFormTests.post.id}/')
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostFormTests.post.id}))
        self.assertEqual(
            response.context['form'].instance.id, PostFormTests.post.id
        )

    def test_authorized_client_can_create_comments(self):
        """Проверяем, что авторизованный пользователь может
        создать комметарий к посту."""
        comments_count = Comment.objects.count()
        new_comment_count = 1
        form_data = {
            'text': 'Текст комментария из формы',
            'post_id': PostFormTests.post.id
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment', kwargs={'post_id': PostFormTests.post.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(
            Comment.objects.count(), comments_count + new_comment_count
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response,
                             f'/posts/{PostFormTests.post.id}/')
        self.assertTrue(
            Comment.objects.filter(
                text='Текст комментария из формы',
            ).exists()
        )
