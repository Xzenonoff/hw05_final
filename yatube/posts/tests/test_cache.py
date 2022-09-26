from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Post, User


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='test text',
        )

    def setUp(self):
        self.guest_client = Client()

    def test_index_cache(self):
        """Тест кеширование главной страницы."""
        response = self.guest_client.get('/')
        CacheTest.post.delete()
        response_1 = self.guest_client.get('/')
        self.assertEqual(response.content, response_1.content)
        cache.clear
        response_2 = self.guest_client.get('/')
        self.assertEqual(response.content, response_2.content)
