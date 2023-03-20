import tempfile
import shutil

from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Post, Group, Comment, Follow

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем пользователей
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='User')
        cls.author = User.objects.create_user(username='Author')
        # Авторизуем пользователей
        cls.authorized_user = Client()
        cls.authorized_user.force_login(cls.user)
        cls.authorized_author = Client()
        cls.authorized_author.force_login(cls.author)
        # Создадим в БД группы
        cls.group_1 = Group.objects.create(
            title='Тестовая группа 1',
            slug='test-slug-1',
            description='Тестовое описание',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-2',
            description='Тестовое описание',
        )
        # Создадим изображение для постов
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        # Создадим в БД 13 постов 1-й группы, автор 'User'
        count = range(0, 13)
        for i in count:
            cls.post = Post.objects.create(
                author=cls.user,
                text='Тестовый пост',
                image=cls.uploaded,
                group=cls.group_1,
            )
        # Создадим в БД 13 постов 2-й группы, автор 'Author'
        count = range(0, 13)
        for i in count:
            cls.post = Post.objects.create(
                author=cls.author,
                text='Тестовый пост',
                image=cls.uploaded,
                group=cls.group_2,
            )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        # Что бы не ругался flake8
        # (Пробовал переделывать (инвертировать) словарь - не помогает)
        post_create_template_for_edit = 'posts/post_create.html'
        post_create_template_for_create = 'posts/post_create.html'

        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': (
                reverse('posts:group_list', kwargs={'slug': 'test-slug-2'})
            ),
            'posts/profile.html': (
                reverse('posts:profile', kwargs={'username': 'Author'})
            ),
            'posts/post_detail.html': (
                reverse('posts:post_detail', kwargs={'post_id': '1'})
            ),
            post_create_template_for_edit: (
                reverse('posts:post_edit', kwargs={'post_id': '1'})
            ),
            post_create_template_for_create: reverse('posts:post_create'),
        }
        cache.clear()
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context_and_use_paginator(self):
        """Шаблон index сформирован с правильным контекстом
        и использует пажинатор."""

        cache.clear()
        response = self.authorized_author.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

        response = self.authorized_author.get(
            reverse('posts:index')
            + '?page=3'
        )
        self.assertEqual(len(response.context['page_obj']), 6)

        post = response.context.get('page_obj')[1]
        self.assertEqual(post.text, 'Тестовый пост')
        self.assertTrue(post.image)

    def test_group_list_show_correct_context_and_use_paginator(self):
        """Шаблон group_list сформирован с правильным контекстом
        и использует пажинатор."""

        response = self.authorized_author.get(reverse(
            'posts:group_list',
            kwargs={'slug': 'test-slug-1'})
        )
        self.assertEqual(len(response.context['page_obj']), 10)

        response = self.authorized_author.get(reverse(
            'posts:group_list',
            kwargs={'slug': 'test-slug-1'})
            + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 3)

        posts = response.context.get('page_obj')
        for post in posts:
            self.assertEqual(post.group, self.group_1)

        post = response.context.get('page_obj')[1]
        self.assertTrue(post.image)

    def test_profile_show_correct_context_and_use_paginator(self):
        """Шаблон profile сформирован с правильным контекстом
        и использует пажинатор."""

        response = self.authorized_author.get(reverse(
            'posts:profile',
            kwargs={'username': 'User'})
        )
        self.assertEqual(len(response.context['page_obj']), 10)

        response = self.authorized_author.get(reverse(
            'posts:profile',
            kwargs={'username': 'User'})
            + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 3)

        posts = response.context.get('page_obj')
        for post in posts:
            self.assertEqual(post.author, self.user)

        post = response.context.get('page_obj')[1]
        self.assertTrue(post.image)

    def test_post_detail_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""

        response = self.authorized_author.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': 13})
        )

        self.assertEqual(response.context['post'].text, 'Тестовый пост')
        self.assertTrue(response.context['post'].image)

    def test_post_edit_correct_context(self):
        """Шаблон post_create (edit) сформирован с правильным контекстом."""

        response = self.authorized_author.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': 14})
        )

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""

        response = self.authorized_author.get(reverse('posts:post_create'))

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_add_comment_only_authorized(self):
        """Добавление комментариев (add_comment) доступно
        только авторизованному клиенту."""

        comments_count = Comment.objects.count()

        form_data = {
            'text': 'Тестовый комментарий',
        }
        self.guest_client.post(
            reverse('posts:add_comment', args=('1')),
            data=form_data,
            follow=True
        )

        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertFalse(
            Comment.objects.filter(
                text='Тестовый комментарий'
            ).exists()
        )

    def test_cache_index(self):
        """Для главной страницы (index) применяется хранение кеша."""

        response = self.authorized_author.get(reverse('posts:index'))
        posts = response.content

        Post.objects.create(
            text='test_new_post',
            author=self.author,
        )

        response_old = self.authorized_author.get(reverse('posts:index'))
        old_posts = response_old.content

        self.assertEqual(old_posts, posts)

        cache.clear()
        response_new = self.authorized_author.get(reverse('posts:index'))
        new_posts = response_new.content

        self.assertNotEqual(old_posts, new_posts)

    def test_add_or_remove_follow(self):
        """Авторизованный пользователь может подписываться на
        других пользователей и удалять их из подписок."""

        # Follow
        self.authorized_user.get(reverse(
            'posts:profile_follow',
            kwargs={'username': 'Author'})
        )

        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.author
            ).exists()
        )

        # Unfollow
        self.authorized_user.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': 'Author'})
        )

        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.author
            ).exists()
        )

    def test_post_in_follow(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан."""

        # Подписываем User на Author
        Follow.objects.create(user=self.user, author=self.author)

        # User заходит на страницу "Избранных авторов"
        response = self.authorized_user.get(reverse('posts:follow_index'))

        # У нас уже заготовлены посты, авторами которых
        # указаны и Author, и User. Если что-то пойдёт не так,
        # на странице follow будут не только записи Author'а.
        posts = response.context.get('page_obj')
        for post in posts:
            self.assertEqual(post.author, self.author)
