from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from posts.models import Post, Group
from django.urls import reverse
from django.core.cache import cache

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            id=1
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем пользователя
        self.somebody = User.objects.create_user(username='SomeBodyToLove')
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.somebody)
        self.templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': '/group/test-slug/',
            'posts/profile.html': '/profile/auth/',
            'posts/post_detail.html': '/posts/1/',
        }
        cache.clear()

    def test_urls_uses_correct_template_when_authorised(self):
        for template, address in self.templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_when_not_authorised(self):
        for template, address in self.templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_for_authorised(self):
        templates_url_names = {
            'posts/create_post.html': '/create/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_for_owner(self):
        templates_url_names = {
            'posts/create_post.html': '/posts/1/edit/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_unexisting_page_404(self):
        response = self.guest_client.get('/unexisting/')
        self.assertEqual(response.status_code, 404)

    def test_create_for_guest_client(self):
        response = self.guest_client.get('/create/')
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_urls_edit_for_author_correct_template(self):
        author_templates_url_names = {
            'posts/create_post.html': '/posts/1/edit/',
        }
        for template, address in author_templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_edit_for_guest_correct_template(self):
        author_templates_url_names = {
            'posts/create_post.html': '/posts/1/edit/',
        }
        for template, address in author_templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateNotUsed(response, template)

    def test_comment_only_users(self):
        data_user = {
            'text': 'я пользователь!'
        }
        data_guest = {
            'text': 'а я мимо проходил'
        }
        response_user = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=data_user,
            follow=True
        )
        response_guest = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=data_guest,
            follow=True
        )
        self.assertRedirects(
            response_guest, '/auth/login/?next=/posts/1/comment/'
        )
        self.assertAlmostEqual(response_user.status_code, 200)
