import shutil
import tempfile
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from posts.models import Post, Group, Follow
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
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
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded,
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        templates_pages_names = {
            reverse('posts:main'): 'posts/index.html',
            reverse(
                'posts:group_posts', kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': self.user}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}
            ): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_detail_show_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id
                    }))
        context = response.context
        post = context['post']
        self.assertEqual(post, self.post)

    def test_edit_uses_correct_form(self):
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={
                'post_id': self.post.id}
        ))
        form_fields = {
            'text': forms.fields.CharField,
        }
        for field_name, type in form_fields.items():
            with self.subTest(key=field_name):
                form_field = response.context['form'].fields[field_name]
                self.assertIsInstance(form_field, type)

    def test_create_uses_correct_form(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }
        for field_name, field_type in form_fields.items():
            with self.subTest(field_name=field_name):
                form_field = response.context['form'].fields[field_name]
                self.assertIsInstance(form_field, field_type)

    def test_post_in_right_places(self):
        post = Post.objects.create(
            text='Новый пост',
            group=self.group,
            author=self.user
        )
        response_new = self.authorized_client.get(reverse('posts:main'))
        response_new_list = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}))
        response_new_profile = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user}))
        context_index = response_new.context['page_obj'][0]
        context_group = response_new_list.context['page_obj'][0]
        context_profile = response_new_profile.context['page_obj'][0]
        self.assertEqual(post, context_index)
        self.assertEqual(post, context_group)
        self.assertEqual(post, context_profile)

    def test_post_in_right_group(self):
        response_index = self.authorized_client.get(reverse('posts:main'))
        response_group_posts = self.authorized_client.get(
            reverse('posts:group_posts',
                    kwargs={'slug': self.group.slug})
        )
        response_profile = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        context_index = response_index.context['page_obj'][0]
        context_group = response_group_posts.context['page_obj'][0]
        context_profile = response_profile.context['page_obj'][0]
        self.assertNotEqual(PostViewsTests, context_index)
        self.assertNotEqual(PostViewsTests, context_group)
        self.assertNotEqual(PostViewsTests, context_profile)

    def test_image_to_context(self):
        field_templates = {
            reverse('posts:main'),
            reverse('posts:profile',
                    kwargs={'username': self.post.author.username}),
            reverse('posts:group_posts',
                    kwargs={'slug': self.group.slug}),
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id})
        }
        for address in field_templates:
            with self.subTest(address=address):
                self.assertTrue(
                    Post.objects.filter(
                        image='posts/small.gif'
                    ).exists()
                )

    def test_core_404_uses_correct_template(self):
        template_name = {
            reverse(
                'posts:profile', kwargs={'username': self.user}
            ): 'posts/profile.html',
        }
        for reverse_name, template in template_name.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        for i in range(15):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост{i}',
                group=cls.group,
            )

    def setUp(self):
        self.guest_client = Client()
        cache.clear()

    def test_first_page_contains_ten_records(self):
        paginator_pages = {
            reverse('posts:main'),
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user})
        }
        for address in paginator_pages:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                context_page = response.context['page_obj']
                self.assertEqual(len(context_page), 10)

    def test_second_page_contains_five_records(self):
        paginator_pages = {
            reverse('posts:main'),
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user})
        }
        for address in paginator_pages:
            with self.subTest(address=address):
                response = self.guest_client.get(address + '?page=2')
                context_page = response.context['page_obj']
                self.assertEqual(len(context_page), 5)


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


class FollowerViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.follower = User.objects.create_user(username='follower')
        cls.not_follower = User.objects.create_user(username='not_follower')
        cls.post = Post.objects.create(
            author=cls.author,
            text='первый пост'
        )

    def setUp(self):
        self.not_follower_client = Client()
        self.follower_client = Client()
        self.follower_client.force_login(self.follower)
        self.not_follower_client = Client()
        self.not_follower_client.force_login(self.not_follower)
        cache.clear()

    def test_authorized_user_follow_unfollow_author(self):
        Follow.objects.create(
            author=self.author,
            user=self.follower
        )
        self.assertTrue(
            Follow.objects.filter(author=self.author, user=self.follower)
        )
        Follow.objects.get(
            author=self.author, user=self.follower
        ).delete()
        self.assertFalse(
            Follow.objects.filter(author=self.author, user=self.follower)
        )

    def test_only_follower_see_author_post(self):
        Follow.objects.create(
            author=self.author,
            user=self.follower
        )
        response_follower = self.follower_client.get(
            reverse('posts:follow_index')
        )
        context_follower = response_follower.context['page_obj'][0]
        response_not_follower = self.not_follower_client.get(
            reverse('posts:follow_index')
        )
        context_not_follower = response_not_follower.context['page_obj']
        self.assertEqual(self.post, context_follower)
        self.assertNotEqual(self.post, context_not_follower)
