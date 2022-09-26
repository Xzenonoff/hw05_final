import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='тестовый текст',
            group=cls.group
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.form_data = {
            'text': 'тестовый текст',
            'group': cls.group.id,
            'image': uploaded
        }
        cls.comment_form_data = {
            'text': 'test comment'
        }
        cls.post_create_rev = reverse('posts:post_create')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_user = Client()
        self.authorized_user.force_login(PostPagesTests.user)

    def test_create_post_in_form(self):
        """Тест на создание поста в БД."""
        num_of_posts = Post.objects.count()
        self.authorized_user.post(
            PostPagesTests.post_create_rev,
            PostPagesTests.form_data
        )
        self.assertTrue(Post.objects.filter(
            author=PostPagesTests.user,
            text='тестовый текст',
            group=PostPagesTests.group.id,
        ).exists())
        new_post = Post.objects.first()
        pairs_for_test = [
            (Post.objects.count(), num_of_posts + 1),
            (new_post.text, PostPagesTests.form_data['text']),
            (new_post.author, PostPagesTests.user),
            (new_post.group.id, PostPagesTests.form_data['group']),
            (new_post.image.name, 'posts/small.gif'),
        ]
        for response, expected in pairs_for_test:
            with self.subTest(response=response):
                self.assertEqual(response, expected)

    def test_edit_post_in_form_and_group_change(self):
        """Тест на проверку редактирования поста и изменения группы поста."""
        post_edit_reverse = reverse(
            'posts:post_edit', kwargs={'post_id': PostPagesTests.post.id}
        )
        group2 = Group.objects.create(
            title='Группа 2',
            slug='test-slug2'
        )
        form_data_edit = {
            'text': 'Новый текст',
            'group': group2.id,
            'id': PostPagesTests.post.id
        }
        self.authorized_user.post(post_edit_reverse, form_data_edit)
        response = self.authorized_user.get(post_edit_reverse)
        self.assertEqual(response.context['post'].text, 'Новый текст')
        self.assertFalse(Post.objects.filter(
            text='Новый текст',
            group=PostPagesTests.group.id,
            id=PostPagesTests.post.id
        ).exists())
        self.assertTrue(Post.objects.filter(
            text='Новый текст',
            group=group2.id,
            id=PostPagesTests.post.id
        ).exists())

    def test_edit_and_create_post_guest(self):
        """
        Тест на проверку создания поста
        для незарегистрированного пользователя.
        """
        response = self.guest_client.post(
            PostPagesTests.post_create_rev, PostPagesTests.form_data
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_comment_auth_user(self):
        """Тест на создание комментария авторизованным пользователем."""
        response = self.authorized_user.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': f'{PostPagesTests.post.id}'}
            ),
            PostPagesTests.comment_form_data
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{PostPagesTests.post.id}'}
            )
        )
        self.assertTrue(
            Comment.objects.filter(
                text='test comment',
            ).exists()
        )

    def test_comment_quest_client(self):
        """Тест на создание комментария неавторизованным пользователем."""
        self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': f'{PostPagesTests.post.id}'}
            ),
            PostPagesTests.comment_form_data
        )
        self.assertFalse(
            Comment.objects.filter(
                text='test comment',
            ).exists()
        )
