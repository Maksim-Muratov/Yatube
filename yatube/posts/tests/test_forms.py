import tempfile
import shutil

from posts.models import Post, Comment
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаём гостевой и авторизованный клиенты
        cls.guest_client = Client()
        cls.author = User.objects.create_user(username='Author')
        cls.authorized_author = Client()
        cls.authorized_author.force_login(cls.author)
        # Создаём необходимые фикстуры:
        # Изображение
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
        # Пост
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""

        posts_count = Post.objects.count()

        form_data = {
            'text': 'Тестовый текст',
            'image': self.uploaded,
        }
        self.authorized_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                image='posts/small.gif'
            ).exists()
        )

    def test_edit_post(self):
        """Валидная форма редактирует существующую в Post запись."""

        posts_count = Post.objects.count()

        form_data = {
            'text': 'тскет йывотсеТ',
        }
        self.authorized_author.post(
            reverse('posts:post_edit', args=('1')),
            data=form_data,
            follow=True
        )

        self.assertEqual(Post.objects.count(), posts_count)
        self.post.refresh_from_db()
        self.assertEqual(self.post.text, 'тскет йывотсеТ')

    def test_add_comment(self):
        """Валидная форма добавляет комментарий (Comment)
        к существующей записи в Post."""

        comments_count = Comment.objects.count()

        form_data = {
            'text': 'Тестовый комментарий',
        }
        self.authorized_author.post(
            reverse('posts:add_comment', args=('1')),
            data=form_data,
            follow=True
        )

        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text='Тестовый комментарий'
            ).exists()
        )
