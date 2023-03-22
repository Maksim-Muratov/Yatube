from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.core.cache import cache

from posts.models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем неавторизованный клиент (гость)
        cls.guest_client = Client()
        # Создаем и авторизуем клиент (зарегистрированный пользователь)
        cls.user = User.objects.create_user(username='HasNoName')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        # Создаем и авторизуем пользователя (автора поста)
        cls.author = User.objects.create_user(username='Author')
        cls.authorized_author = Client()
        cls.authorized_author.force_login(cls.author)
        # Создадим запись автора в БД
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )

    def test_404_error(self):
        """При запросе несуществующей страницы выпадает ошибка 404,
        отображаемая на кастомном шаблоне."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_url_available_to_any_user(self):
        """Страница доступна любому пользователю."""
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': '/group/test-slug/',
            'posts/profile.html': '/profile/HasNoName/',
            'posts/post_detail.html': '/posts/1/',
        }
        cache.clear()
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, 200)

    def test_url_available_only_to_an_authorized_user(self):
        """Страница доступна только авторизованному пользователю.
        Неавторизованный перенаправляется на страницу логина"""

        templates_url_names = {
            'posts/post_create.html': '/create/',
            'posts/follow.html': '/follow/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, 200)

        redirect_url_names = {
            '/auth/login/?next=/create/': '/create/',
            '/auth/login/?next=/follow/': '/follow/',
        }
        for redirect, address in redirect_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertRedirects(response, redirect)

    def test_url_available_only_to_an_author(self):
        """Страница доступна только автору.
        Другой пользователь перенаправляются на страницу
        подробной информации о посте"""
        template = 'posts/post_create.html'
        address = '/posts/1/edit/'

        response = self.authorized_author.get(address)
        self.assertTemplateUsed(response, template)
        self.assertEqual(response.status_code, 200)

        response = self.authorized_client.get(address)
        self.assertRedirects(response, '/posts/1/')
