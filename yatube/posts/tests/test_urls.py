from http import HTTPStatus

from django.test import Client, TestCase

from ..models import Group, Post, User


class StaticURLTests(TestCase):
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
            text='Тестовый текст',
            group=cls.group
        )
        cls.public_addresses = [
            ('posts/index.html', '/'),
            ('posts/group_list.html', f'/group/{cls.group.slug}/'),
            ('posts/profile.html', f'/profile/{cls.post.author}/'),
            ('posts/post_detail.html', f'/posts/{cls.post.id}/'),
        ]
        cls.private_addresses = [
            ('posts/create_post.html', '/create/'),
            (
                'posts/create_post.html',
                f'/posts/{cls.post.id}/edit/'
            ),
        ]

    def setUp(self):
        self.guest_client = Client()
        self.authorized_user = Client()
        self.authorized_user.force_login(StaticURLTests.user)

    def test_urls_for_guest_public(self):
        """Тест публичных URL для неавторизованного пользователя."""
        for template, address in StaticURLTests.public_addresses:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_for_guest_private(self):
        """Тест приватных URL для неавторизованного пользователя."""
        for template, address in StaticURLTests.private_addresses:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_urls_for_auth_client(self):
        """Тест URL для авторизованного пользователя."""
        urls = (
            StaticURLTests.public_addresses + StaticURLTests.private_addresses
        )
        for template, address in urls:
            with self.subTest(address=address):
                response = self.authorized_user.get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_create_post_and_edit(self):
        addresses = []
        for template, url in StaticURLTests.private_addresses:
            addresses.append(url)
        for address in addresses:
            with self.subTest(address=address):
                response_guest = self.guest_client.get(address)
                self.assertEqual(response_guest.status_code, HTTPStatus.FOUND)
                self.assertRedirects(
                    response_guest,
                    f'/auth/login/?next={address}'
                )

                response_auth = self.authorized_user.get(address)
                self.assertEqual(response_auth.status_code, HTTPStatus.OK)

    def test_urls_unexisting_page(self):
        response = self.guest_client.get('/random_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
