from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

User = get_user_model()


class UserURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/auth/login/': 'users/login.html',
            '/auth/signup/': 'users/signup.html',
            '/auth/password_change/': 'users/password_change_form.html',
            '/auth/password_change/done/': 'users/password_change_done.html',
            '/auth/password_reset/': 'users/password_reset_form.html',
            '/auth/reset/<uidb64>/<token>/':
                'users/password_reset_confirm.html',
            '/auth/reset/done/': 'users/password_reset_complete.html',
            '/auth/password_reset/done/': 'users/password_reset_done.html',
            '/auth/logout/': 'users/logged_out.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_authorised_user_availability(self):
        """URL-адреса доступны авторизованному пользователю."""
        urls = [
            '/auth/login/', '/auth/signup/', '/auth/password_change/',
            '/auth/password_change/done/', '/auth/password_reset/',
            '/auth/reset/<uidb64>/<token>/', '/auth/reset/done/',
            '/auth/password_reset/done/', '/auth/logout/'
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_unauthorised_user_availability(self):
        """При обращении на URL-адреса не доступны не авторизованному
        пользователю происходит редирект на авторизацию."""
        response = self.guest_client.get('/auth/password_change/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/auth/password_change/'
        )
