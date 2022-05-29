# Тесты форм
# posts/tests/test_forms.py
import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post, User

URL_POST_CREATE = reverse('posts:post_create')
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = PostForm()
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(username='Author')
        self.non_autorized_user = Client()
        self.autorized_author = Client()
        self.autorized_author.force_login(self.user)
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        self.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test',
            description='Тестовое описание'
        )
        self.URL_PROFILE = reverse(
            'posts:profile', kwargs={'username': self.user.username}
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cache.clear()

    def test_create_post(self):
        """Тест создания нового поста при отправке формы"""
        posts_count = Post.objects.count()
        form_data = {
            'group': self.group.id,
            'text': 'Тестовый текст',
            'image': self.uploaded,
        }
        response = self.autorized_author.post(
            URL_POST_CREATE,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, self.URL_PROFILE)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                image=f'posts/{self.uploaded.name}'
            ).exists()
        )
        last_post_id = Post.objects.latest('id')
        self.assertNotEqual(
            last_post_id.id, posts_count
        )

    def test_edit_post(self):
        """Тест изменения поста при отправке формы"""
        form_data = {
            'group': f'{self.group.id}',
            'text': 'Тестовый текст',
        }
        edit_form_data = {
            'group': f'{self.group.id}',
            'text': 'Изменённый Тестовый текст',
        }
        response = self.autorized_author.post(
            URL_POST_CREATE,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, self.URL_PROFILE)
        self.old_post = Post.objects.get(
            id=((response.context.get('page_obj').object_list)[0]).id
        )
        URL_EDIT_POST = reverse(
            'posts:post_edit', kwargs={'post_id': self.old_post.id}
        )
        response = self.autorized_author.post(
            URL_EDIT_POST,
            data=edit_form_data,
            follow=True
        )
        new_post = Post.objects.get(id=self.old_post.id)
        self.old_post_id = self.old_post.id
        self.assertNotEqual(self.old_post.text, new_post.text)

    def test_create_comment(self):
        """Тест комментирование"""
        form_data = {
            'group': f'{self.group.id}',
            'text': 'Тестовый текст',
        }
        self.autorized_author.post(
            URL_POST_CREATE,
            data=form_data,
            follow=True
        )
        # Новый пост
        last_post = Post.objects.latest('id')
        last_post_id = (last_post).id
        URL_COMMENT = reverse(
            'posts:add_comment',
            kwargs={
                "post_id": last_post_id
            }
        )
        response = self.autorized_author.get(URL_COMMENT)
        self.assertEqual(response.url, f"/posts/{last_post_id}/")
        # авторизованный пишет
        response = self.non_autorized_user.get(URL_COMMENT)
        self.assertEqual(
            response.url,
            f'/auth/login/?next=/posts/{last_post_id}/comment/'
        )
        # если нет, то авторизоваться для начала
