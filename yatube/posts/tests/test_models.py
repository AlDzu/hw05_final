# Тесты моделей
# posts/tests/test_models.py
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from posts.models import Comment, Follow, Group, Post

User = get_user_model()


class PostsModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()
        cls.user = User.objects.create_user(username='auth')
        cls.user2 = User.objects.create_user(username='auth2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий',
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.user2,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cache.clear()

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostsModelTest.group
        verbose = group.title
        self.assertEqual(verbose, 'Тестовая группа')
        verbose = group.slug
        self.assertEqual(verbose, 'Тестовый слаг')
        verbose = group.description
        self.assertEqual(verbose, 'Тестовое описание')

        post = PostsModelTest.post
        verbose = post.author.username
        self.assertEqual(verbose, 'auth')
        verbose = post.text
        self.assertEqual(verbose, 'Тестовая пост')

        comment = PostsModelTest.comment
        verbose = comment.text
        self.assertEqual(verbose, 'Тестовый комментарий')

        follow = PostsModelTest.follow
        verbose = follow._meta.get_field('user').verbose_name
        self.assertEqual(verbose, 'Который подписывается')
        verbose = follow._meta.get_field('author').verbose_name
        self.assertEqual(verbose, 'На которого подписываются')
