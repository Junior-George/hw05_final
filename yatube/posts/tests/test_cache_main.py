from django.core.cache import cache
from django.test import Client
from django.test import TestCase
from django.urls import reverse
from posts.models import Post
from posts.models import User


class TestaCache(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Просто название'
        )

    def setUp(self):
        self.guest_client = Client()
        self.main = reverse('posts:main')

    def test_cache_index(self):
        """ Тестируем, что в кэш добавляется и удалается пост """
        get_obj = self.guest_client.get(self.main)
        Post.objects.filter(
            text='Просто название',
            author=self.user,
        ).delete()
        get_obj_1 = self.guest_client.get(self.main)
        self.assertEqual(get_obj.content, get_obj_1.content)

        cache.clear()

        get_obj_2 = self.guest_client.get(self.main)
        self.assertNotEqual(get_obj_1.content, get_obj_2.content)
