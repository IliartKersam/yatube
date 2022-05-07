from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus

User = get_user_model()


class NewUserTests(TestCase):
    """Протестируем, что добавляется новый пользователь."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='First')

    def setUp(self):
        self.guest_client = Client()

    def test_can_create_user(self):
        """Проверяем что создается новый юзер."""
        new_user_count = 1
        user_count = User.objects.count()
        form_data = {
            'first_name': 'Jon',
            'last_name': 'Snow',
            'username': 'second',
            'email': 'targarian@winterfel.com',
            'password1': '4Thdffgj7l',
            'password2': '4Thdffgj7l'
        }
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        self.assertEqual(User.objects.count(), user_count + new_user_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, '/')
