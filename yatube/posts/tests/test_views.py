# Тесты представлений
# posts/tests/test_views.py
import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment
from posts.settings import NUMBER_OF_POSTS
from posts.views import Follow, Group, Post, PostForm, User

URL_INDEX = reverse('posts:index')
URL_CREATE_POST = reverse('posts:post_create')
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
URL_FOLLOW_INDEX = reverse('posts:follow_index')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()
        cls.user = User.objects.create_user(username='Author')
        cls.autorized_author = Client()
        cls.autorized_author.force_login(cls.user)
        cls.user2 = User.objects.create_user(username='Author2')
        cls.user3 = User.objects.create_user(username='Author3')
        cls.autorized_author2 = Client()
        cls.autorized_author2.force_login(cls.user3)
        cls.URL_PROFILE = reverse(
            'posts:profile', kwargs={'username': cls.user.username}
        )
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test',
            description='Тестовое описание'
        )
        cls.group2 = Group.objects.create(
            title='Тестовый заголовок2',
            slug='test2',
            description='Тестовое описание2'
        )
        cls.URL_POSTS_GROUP = reverse(
            'posts:group', kwargs={'slug': cls.group.slug}
        )
        cls.URL_POSTS_GROUP_2 = reverse(
            'posts:group', kwargs={'slug': cls.group2.slug}
        )
        cls.URL_FOLLOW = reverse(
            'posts:profile_follow',
            kwargs={"username": cls.user2.username}
        )
        cls.URL_UNFOLLOW = reverse(
            "posts:profile_unfollow",
            kwargs={"username": cls.user2.username}
        )

        objs = (Post(
            text='Тестовый текст %s' % i, author=cls.user, group=cls.group
        ) for i in range(1, 12)
        )
        bulk_data = list(objs)
        Post.objects.bulk_create(bulk_data)
        cls.post = Post.objects.first()
        cls.post3 = Post.objects.create(
            text='Тестовый текст группы два',
            author=cls.user2,
            group=cls.group2,
        )
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

        cls.post2 = Post.objects.create(
            text='Тестовый текст последнего поста',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded  # с картинкой
        )
        cls.URL_POST_DETAIL = reverse(
            'posts:post_detail', kwargs={'post_id': f'{cls.post.id}'}
        )
        cls.URL_POST_2_DETAIL = reverse(
            'posts:post_detail', kwargs={'post_id': f'{cls.post2.id}'}
        )

        cls.URL_POST_EDIT = reverse(
            'posts:post_edit', kwargs={'post_id': f'{cls.post.id}'}
        )
        cls.URL_COMMENT = reverse(
            'posts:add_comment',
            kwargs={
                "post_id": f'{cls.post2.id}'
            }
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        cache.clear()

    def test_index_true_template(self):
        """Урл использует верный шаблон"""
        templates_pages_names = {
            'posts/index.html': URL_INDEX,
            'posts/group_list.html': self.URL_POSTS_GROUP,
            'posts/profile.html': self.URL_PROFILE,
            'posts/post_detail.html': self.URL_POST_DETAIL,
            'posts/create_post.html': URL_CREATE_POST,
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                cache.clear()
                response = self.autorized_author.get(reverse_name)
                self.assertTemplateUsed(response, template)
        response = self.autorized_author.get(self.URL_POST_EDIT)
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_true_index(self):
        """Главная страница"""
        cache.clear()
        response = self.autorized_author.get(URL_INDEX)
        self.assertEqual(len(response.context['page_obj']), NUMBER_OF_POSTS)
        response = self.autorized_author.get(
            URL_INDEX + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_true_group_posts(self):
        """Посты по группам + пагинатор"""
        response = self.autorized_author.get(self.URL_POSTS_GROUP)
        self.assertEqual(response.context.get(
            'group').title, 'Тестовый заголовок')
        self.assertEqual(len(response.context['page_obj']), NUMBER_OF_POSTS)
        response = self.autorized_author.get(
            self.URL_POSTS_GROUP + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 2)

    def test_true_user_posts(self):
        """Посты по пользователю"""
        response = self.autorized_author.get(self.URL_PROFILE)
        self.assertEqual(
            response.context.get('user_info').username, self.user.username
        )
        self.assertEqual(len(response.context['page_obj']), NUMBER_OF_POSTS)
        response = self.autorized_author.get(
            self.URL_PROFILE + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 2)

    def test_true_id_post(self):
        """Пост по ид"""
        response = self.autorized_author.get(self.URL_POST_DETAIL)
        self.assertEqual(
            response.context.get('selected_post').text,
            f'Тестовый текст {self.post.id}'
        )

    def test_true_edit_post(self):
        """Форма редактирования поста по ид"""
        response = self.autorized_author.get(self.URL_POST_EDIT)
        form_field = response.context.get('form')
        self.assertIsInstance(form_field, PostForm)
        post_field = response.context.get('post')
        self.assertIsInstance(post_field, Post)

    def test_true_create_post(self):
        """Создание поста"""
        response = self.autorized_author.get(URL_CREATE_POST)
        form_field = response.context.get('form')
        self.assertIsInstance(form_field, PostForm)

    def test_new_post(self):
        """Тест нового поста"""
        response_index = self.autorized_author.get(URL_INDEX)
        last_post = (response_index.context.get('page_obj').object_list)[0]
        # последний пост
        self.assertEqual(last_post, self.post2)
        # Появился на главной
        response_group = self.autorized_author.get(self.URL_POSTS_GROUP)
        last_post = (response_group.context.get('page_obj').object_list)[0]
        # последний пост
        self.assertEqual(last_post, self.post2)
        # Появился в группах
        response_profile = self.autorized_author.get(self.URL_PROFILE)
        last_post = (response_profile.context.get('page_obj').object_list)[0]
        # последний пост
        self.assertEqual(last_post, self.post2)
        # Появился в профиле
        response_group2 = self.autorized_author.get(self.URL_POSTS_GROUP_2)
        last_post = (response_group2.context.get('page_obj').object_list)[0]
        # последний пост в группе 2
        self.assertNotEqual(last_post, self.post2)
        # Пост группы 1 Не появился в группе 2
        self.assertEqual(last_post, self.post3)
        # Появился в группе 1

    def test_image_on_page(self):
        """Наличие картинки на страницах"""
        # На главной
        response = self.autorized_author.get(URL_INDEX)
        context = (response.context.get('page_obj').object_list)[0]
        self.assertEqual(context.image, self.post2.image)
        # В профайле
        response = self.autorized_author.get(self.URL_PROFILE)
        context = (response.context.get('page_obj').object_list)[0]
        self.assertEqual(context.image, self.post2.image)
        # В группе
        response = self.autorized_author.get(self.URL_POSTS_GROUP)
        context = (response.context.get('page_obj').object_list)[0]
        self.assertEqual(context.image, self.post2.image)
        # На странице поста
        response = self.autorized_author.get(self.URL_POST_2_DETAIL)
        context = response.context.get('selected_post')
        self.assertEqual(context.image, self.post2.image)

    def test_comment_on_post_detail(self):
        """Появление комментария на странице поста"""
        new_comment = Comment.objects.create(
            post=self.post2,
            author=self.user,
            text='Новый комментарий'
        )
        response_comment = self.autorized_author.get(self.URL_POST_2_DETAIL)
        post_comment = response_comment.context.get(
            'selected_post'
        ).comments.all()
        self.assertEqual(new_comment, post_comment[0])

    def test_follow(self):
        """Тест подписки/отписки"""
        self.autorized_author.get(self.URL_FOLLOW)
        self.assertEqual(Follow.objects.count(), 1)
        # Авторизованный подписался
        self.autorized_author.get(self.URL_UNFOLLOW)
        self.assertEqual(Follow.objects.count(), 0)
        cache.clear()
        # Авторизованный отписался

    def test_following_post(self):
        """Тест пявления поста в ленте"""
        self.autorized_author.get(self.URL_FOLLOW)
        response = self.autorized_author.get(URL_FOLLOW_INDEX)
        follow_posts = response.context.get('posts')[0]
        self.assertEqual(follow_posts, self.post3)
        # в ленте кто подписан
        response = self.autorized_author2.get(URL_FOLLOW_INDEX)
        follow_posts = response.context.get('posts')
        self.assertEqual(len(follow_posts), 0)
        # лена неподписанных пуста
