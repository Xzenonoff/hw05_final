from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='test group',
            slug='test slug',
            description='test description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='test text',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        group = PostModelTest.group
        test_items = [
            (group.title, group),
            (post.text[:15], post)
        ]
        for response, expected in test_items:
            with self.subTest(response=response):
                self.assertEqual(response, str(expected))

    def test_verbose_name(self):
        """Проверяем, что у моделей корректно работает verbose_name."""
        post = PostModelTest.post
        field_verbose = [
            ('author', 'Автор'),
            ('pub_date', 'Дата публикации'),
            ('text', 'Текст поста'),
            ('group', 'Группа'),
        ]
        for field, verbose in field_verbose:
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, verbose
                )

    def test_help_text(self):
        """Проверяем, что у моделей корректно работает help_text."""
        post = PostModelTest.post
        field_help = [
            ('text', 'Введите текст поста'),
            ('group', 'Группа, к которой будет относиться пост'),
        ]
        for field, help_t in field_help:
            with self.subTest(field=field):
                self.assertEqual(post._meta.get_field(field).help_text, help_t)
