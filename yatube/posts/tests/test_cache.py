from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from posts.views import Post, User

URL_INDEX = reverse('posts:index')


class IndexCacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()
        cls.user = User.objects.create_user(username='Author')
        cls.autorized_author = Client()
        cls.autorized_author.force_login(cls.user)
        cls.URL_PROFILE = reverse(
            'posts:profile', kwargs={'username': cls.user.username}
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.user,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cache.clear()

    def test_index_cache(self):
        """Тест успешного кэширования"""
        cache.clear()
        response = self.client.get(URL_INDEX)
        test_response = self.client.get(URL_INDEX)
        self.assertIn(self.post, response.context['page_obj'])
        Post.objects.all().delete()
        self.assertNotIn(self.post, Post.objects.all())
        response = self.client.get(URL_INDEX)
        self.assertEqual(test_response.content, response.content)
        cache.clear()
        response = self.client.get(URL_INDEX)
        self.assertNotEqual(test_response.content, response.content)
