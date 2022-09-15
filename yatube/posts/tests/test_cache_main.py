from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post, User


class TestaCache(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='пост'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    def setUp(self):
        self.guest_client = Client()
        self.main = reverse('posts:main')

    def test_cache_index(self):
        get_obj = self.guest_client.get(self.main)
        Post.objects.create(
            text='Новый текст',
            author=self.user,
            group=self.group
        )
        get_obj_2 = self.guest_client.get(self.main)
        self.assertEqual(get_obj.content, get_obj_2.content)

        cache.clear()

        get_obj_3 = self.guest_client.get(self.main)
        self.assertNotEqual(
            get_obj.content or get_obj_2.content, get_obj_3.content
        )
