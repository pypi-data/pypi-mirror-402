import unittest

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase
from django.urls import reverse

from django_oidc_admin.authentication import DjangoOIDCAdminBackend, DjangoOIDCAdminCallbackView
from django_oidc_admin.context_processors import admin_navbar

User = get_user_model()

class MessagingRequest(HttpRequest):
    """
    Custom request class to store messages in a list.
    Messages are not stored in the request object when using the classic RequestFactory.
    """
    session = 'session'

    def __init__(self):
        super(MessagingRequest, self).__init__()
        self._messages = FallbackStorage(self)

    def get_messages(self):
        return getattr(self._messages, '_queued_messages')

    def get_message_strings(self):
        return [str(m) for m in self.get_messages()]

class TestDjangoMozillaOIDCCustomBackend(TestCase):

    def setUp(self):
        self.backend = DjangoOIDCAdminBackend()
        self.group = Group.objects.create(name="Users")
        self.claims = {
            "email": "test@example.com",
            "preferred_username": "testuser",
            "name": "Test User",
            "given_name": "Test"
        }

    def test_creates_user_with_valid_claims(self):
        user = self.backend.create_user(self.claims)
        self.assertIsNotNone(user)
        self.assertEqual(user.email, self.claims["email"])
        self.assertEqual(user.username, self.claims["preferred_username"])
        self.assertEqual(user.first_name, self.claims["given_name"])
        self.assertEqual(user.last_name, self.claims["name"])
        self.assertFalse(user.is_active)  # User is inactive by default
        self.assertTrue(user.groups.filter(name="Users").exists())

    def test_does_not_create_user_without_email(self):
        claims = {"preferred_username": "testuser"}
        user = self.backend.create_user(claims)
        self.assertIsNone(user)

    def test_filters_users_by_email(self):
        User.objects.create_user(username="testuser", email="test@example.com")
        users = self.backend.filter_users_by_claims(self.claims)
        self.assertEqual(users.count(), 1)
        self.assertEqual(users.first().email, self.claims["email"])

    def test_does_not_filter_users_without_email(self):
        claims = {"preferred_username": "testuser"}
        users = self.backend.filter_users_by_claims(claims)
        self.assertEqual(users.count(), 0)

class TestDjangoMozillaOIDCCustomCallbackView(unittest.TestCase):

    def setUp(self):
        self.callback_view = DjangoOIDCAdminCallbackView()
        self.factory = RequestFactory()

    def test_redirects_to_login_on_login_failure(self):
        self.factory.get(reverse("oidc_authentication_callback"))
        response = self.callback_view.login_failure()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.callback_view.failure_url)

    def test_shows_warning_message_for_inactive_user(self):
        request = MessagingRequest()  # Message Middleware does not work with RequestFactory
        user = User.objects.create_user(username="testuser", email="test@example.com", is_active=False)
        self.callback_view.user = user
        response = self.callback_view.get(request)
        self.assertEqual(response.status_code, 302)
        self.assertIn("Your account has been created and is pending validation.", request.get_message_strings()[0])

class TestAdminNavbarContextProcessor(unittest.TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def test_returns_pending_sso_users_for_staff_user(self):
        request = self.factory.get('/')
        request.user = User.objects.create_user(username='staffuser', is_staff=True)
        User.objects.create_user(username='inactiveuser1', is_active=False)
        User.objects.create_user(username='inactiveuser2', is_active=False)
        context = admin_navbar(request)
        self.assertEqual(context['pending_sso_users'], 2)

    def test_returns_empty_context_for_non_staff_user(self):
        request = self.factory.get('/')
        request.user = User.objects.create_user(username='regularuser', is_staff=False)
        context = admin_navbar(request)
        self.assertEqual(context, {})

    def test_returns_empty_context_for_anonymous_user(self):
        request = self.factory.get('/')
        request.user = User()
        context = admin_navbar(request)
        self.assertEqual(context, {})


class TestAdminBaseTemplate(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='admin', is_staff=True, is_active=True, is_superuser=True)
        self.template_name = 'admin/base.html'

    @unittest.skip("Not working at the moment")
    def test_renders_form_for_pending_sso_users_with_permission(self):
        self.client.force_login(self.user)
        request = self.factory.get('/')
        request.user = self.user

        context = {
            'pending_sso_users': 3,
            'perms': {'auth': {'change_user': True}},
            'request': request,
        }

        rendered = render_to_string(self.template_name, context)
        self.assertIn('<form class="to-sso-users-form"', rendered)


    def test_does_not_render_form_without_pending_sso_users(self):
        self.client.force_login(self.user)
        request = self.factory.get('/')
        request.user = self.user
        context = {'pending_sso_users': 0, 'perms': {'auth': {'change_user': True}}, 'request': request}
        rendered = render_to_string(self.template_name, context)
        self.assertNotIn('🔔', rendered)

    def test_does_not_render_form_without_permission(self):
        self.client.force_login(self.user)
        request = self.factory.get('/')
        self.user.is_staff = False
        self.user.save()
        request.user = self.user
        context = {'pending_sso_users': 3, 'perms': {'auth': {'change_user': False}}, 'request': request}
        rendered = render_to_string(self.template_name, context)
        self.assertNotIn('🔔', rendered)



class TestAdminLoginTemplate(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.template_name = 'admin/login.html'

    def test_renders_sso_button(self):
        request = self.factory.get('/')
        context = {'request': request}
        rendered = render_to_string(self.template_name, context)
        self.assertIn('Connect with SSO 🪩', rendered)

    def test_sso_button_has_correct_url(self):
        request = self.factory.get('/')
        context = {'request': request}
        rendered = render_to_string(self.template_name, context)
        url = reverse('oidc_authentication_init')
        self.assertIn(f'href="{url}"', rendered)
