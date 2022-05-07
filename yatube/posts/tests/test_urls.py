from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from ..models import Post, Group

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_a = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(title='Тестовая группа',
                                         slug='test_slug',
                                         description='Тестовое описание')
        cls.post = Post.objects.create(author=cls.user_a,
                                       text='Текст тестового поста')
        cls.public_urls = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user_a.username}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
        }
        cls.private_urls = {
            '/create/': 'posts/create_post.html',
        }
        cls.post_edit_url = {
            f'/posts/{cls.post.id}/edit/': 'posts/create_post.html'
        }

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client_a = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_a.force_login(PostsURLTests.user_a)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон.(тестирование
        проводиться для пользователя с максимальными правами доступа,
        в данном случае это авторизованный пользователь, автор поста."""
        for url, template in {
            **PostsURLTests.public_urls, **PostsURLTests.private_urls,
            **PostsURLTests.post_edit_url
        }.items():
            with self.subTest(url=url):
                response = self.authorized_client_a.get(url)
                self.assertTemplateUsed(response, template)

    def test_urls_authorised_user_availability(self):
        """Public и Private URL-адреса доступны
        авторизованному пользователю."""
        for url, _ in {
            **PostsURLTests.public_urls, **PostsURLTests.private_urls
        }.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_unauthorised_user_availability(self):
        """Public URL-адреса доступны не авторизованному пользователю.
        При обращении к Private URL-адресам для не авторизованного
        пользователя происходит редирект на сраницу авторизации."""
        for url, _ in PostsURLTests.public_urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

        for url, _ in PostsURLTests.private_urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, f'/auth/login/?next={url}')

    def test_edit_page_availability(self):
        """При обращении к URL-адресу редактирования поста пользователя не
        автора, будет редирект."""
        for url, _ in PostsURLTests.post_edit_url.items():
            not_author_users = {
                self.guest_client: f'/auth/login/?next={url}',
                self.authorized_client: f'/posts/{PostsURLTests.post.id}/'
            }
            for user, redirect_url in not_author_users.items():
                with self.subTest(user=user):
                    response = user.get(url, follow=True)
                    self.assertRedirects(response, redirect_url)

    def test_urls_unexisting_page(self):
        """При обращении к несуществующей странице появиться ошибка 404."""
        response = self.authorized_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
