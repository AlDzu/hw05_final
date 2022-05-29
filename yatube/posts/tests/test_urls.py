# Тесты адресов
# posts/tests/test_urls.py
from django.core.cache import cache
from django.test import Client, TestCase
from posts.models import Group, Post, User


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()
        cls.user = User.objects.create_user(username='Author')
        cls.autorized_author = Client()
        cls.autorized_author.force_login(cls.user)
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user
        )
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test',
            description='Тестовое описание'
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='TestUser')
        self.autorized_client = Client()
        self.autorized_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cache.clear()

    def test_posts_urls(self):
        """Доступность урлов posts"""

        last_post_id = (Post.objects.latest('id')).id
        urls_templates_all = {
            '': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{last_post_id}/': 'posts/post_detail.html',
        }
        urls_templates_autorised = {
            '/create/': 'posts/create_post.html',
        }
        urls_templates_author = {
            f'/posts/{last_post_id}/edit/': 'posts/create_post.html'
        }

        for url, template in urls_templates_all.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
                cache.clear()
                response = self.autorized_client.get(url)
                self.assertTemplateUsed(response, template)
                cache.clear()

        for url, template in urls_templates_autorised.items():
            with self.subTest(url=url):
                response = self.autorized_client.get(url)
                self.assertTemplateUsed(response, template)

        for url, template in urls_templates_author.items():
            with self.subTest(url=url):
                response = self.autorized_author.get(url)
                self.assertTemplateUsed(response, template)
