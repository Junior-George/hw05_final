from posts.forms import PostForm
from ..models import Post, Comment
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_no_author = User.objects.create_user(username="no_auth")
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.form = PostForm()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_no_auth_client = Client()
        self.authorized_no_auth_client.force_login(self.user_no_author)

    def test_edit_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый текст поста'
        }
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': 1}),
            data=form_data,
            follow=True
        )
        self.assertTrue(
            Post.objects.filter(
                id=1,
                author=self.user,
                text='Новый текст поста',
            ).exists()
        )
        self.assertEqual(posts_count, Post.objects.count())

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый пост в пост креате',
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_comment_exists(self):
        form_data = {
            'text': 'Коммент'
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertTrue(
            Comment.objects.filter(
                text='Коммент',
            ).exists()
        )
