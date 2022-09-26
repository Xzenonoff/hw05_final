import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test')
        cls.follower = User.objects.create(username='follower')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание группы',
            slug='test-slug'
        )
        image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='image',
            content=image,
            content_type='image/jpg'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='тестовый текст',
            group=cls.group,
            pub_date='02.09.2022',
            image=uploaded
        )
        cls.reverses = {
            'index': ('posts/index.html', reverse('posts:index')),
            'group_list': (
                'posts/group_list.html', reverse(
                    'posts:group_list',
                    kwargs={'slug': cls.group.slug}
                )
            ),
            'profile': (
                'posts/profile.html', reverse(
                    'posts:profile',
                    kwargs={'username': cls.post.author.username}
                )
            ),
            'post_detail': (
                'posts/post_detail.html', reverse(
                    'posts:post_detail',
                    kwargs={'post_id': cls.post.id}
                )
            ),
            'post_create': (
                'posts/create_post.html', reverse('posts:post_create')
            ),
            'post_edit': (
                'posts/create_post.html', reverse(
                    'posts:post_edit',
                    kwargs={'post_id': cls.post.id}
                )
            ),
            'follow_index': (
                'posts/follow.html', reverse('posts:follow_index')
            )
        }
        cls.follow_rev = reverse(
            'posts:profile_follow',
            kwargs={'username': cls.user.username}
        )
        cls.unfollow_rev = reverse(
            'posts:profile_unfollow',
            kwargs={'username': cls.user.username}
        )
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        Follow.objects.create(
            user=cls.follower, author=cls.user
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_user = Client()
        self.authorized_user.force_login(PostPagesTests.user)
        self.follower_user = Client()
        self.follower_user.force_login(PostPagesTests.follower)

    def context_post_assert(self, obj):
        self.assertEqual(obj.text, PostPagesTests.post.text)
        self.assertEqual(obj.group, PostPagesTests.post.group)
        self.assertEqual(obj.author, PostPagesTests.post.author)
        self.assertEqual(obj.pub_date, PostPagesTests.post.pub_date)
        self.assertEqual(obj.image, PostPagesTests.post.image)

    def test_pages_uses_correct_template(self):
        """URL использует соответствующий шаблон."""
        for template, reverse_name in PostPagesTests.reverses.values():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_user.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_has_correct_context(self):
        """Тест контекста для index, group_list, profile."""
        urls = (
            PostPagesTests.reverses['index'][1],
            PostPagesTests.reverses['group_list'][1],
            PostPagesTests.reverses['profile'][1]
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_user.get(url)
                self.context_post_assert(response.context['page_obj'][0])

    def test_post_detail_has_correct_context(self):
        """Тест контекста для detail."""
        response = self.authorized_user.get(
            PostPagesTests.reverses['post_detail'][1]
        )
        self.context_post_assert(response.context['post'])
        self.assertEqual(
            response.context['post'].author.posts.count(),
            PostPagesTests.post.author.posts.count()
        )

    def test_create_post_has_correct_context(self):
        """Тест контекста для create."""
        response = self.authorized_user.get(
            PostPagesTests.reverses['post_create'][1]
        )
        for value, expected in PostPagesTests.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_has_correct_context(self):
        """Тест контекста для edit."""
        response = self.authorized_user.get(
            PostPagesTests.reverses['post_edit'][1]
        )
        for value, expected in PostPagesTests.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
                self.assertEqual(response.context['is_edit'], True)

    def test_post_create_group_check(self):
        """Тест добавления поста при указании группы."""
        urls = (
            PostPagesTests.reverses['index'][1],
            PostPagesTests.reverses['group_list'][1],
            PostPagesTests.reverses['profile'][1]
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_user.get(url)
                self.assertEqual(
                    response.context.get('page_obj')[0],
                    PostPagesTests.post,
                    f'{PostPagesTests.post.id}'
                )

    def test_paginator(self):
        """Проверяем, что Paginator работает корректно."""
        objs = [
            Post(
                text=f'текст {i}',
                author=PostPagesTests.user,
                group=PostPagesTests.group,
            ) for i in range(13)
        ]
        Post.objects.bulk_create(objs)
        page_posts = [
            (1, 10),
            (2, 4),
        ]
        urls = (
            PostPagesTests.reverses['index'][1],
            PostPagesTests.reverses['group_list'][1],
            PostPagesTests.reverses['profile'][1]
        )
        for url in urls:
            with self.subTest(url=url):
                for page, post_num in page_posts:
                    response = self.authorized_user.get(url, {'page': page})
                    self.assertEqual(
                        len(response.context['page_obj']), post_num
                    )

    def test_follow_unfollow(self):
        """Тест подписки на пользователей и удаление их из подписок."""
        self.follower_user.post(PostPagesTests.follow_rev)
        self.assertTrue(
            Follow.objects.filter(
                user=PostPagesTests.follower,
                author=PostPagesTests.user
            ).exists()
        )

        self.follower_user.post(PostPagesTests.unfollow_rev)
        self.assertFalse(
            Follow.objects.filter(
                user=PostPagesTests.follower,
                author=PostPagesTests.user
            ).exists()
        )

    def test_correct_follow_showing(self):
        """Тест корректного отображение подписок."""
        follow_index_rev = reverse('posts:follow_index')

        response = self.authorized_user.get(follow_index_rev)
        self.assertNotIn(self.post, response.context['page_obj'])

        response = self.follower_user.get(follow_index_rev)
        self.assertIn(self.post, response.context['page_obj'])
