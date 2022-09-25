from posts.forms import PostForm
from ..models import Post
from ..models import Comment
from django.contrib.auth import get_user_model
from django.test import Client
from django.test import TestCase
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
        self.authorized_client.force_login(PostCreateFormTests.user)

    def test_edit_post(self):
        """ Тестируем функцию изменить пост' """
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
        """ Тестируем добавление поста через .count """
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый пост в пост креате',
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_comment_exists(self):
        """ Тестируем добавление комментария """
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
