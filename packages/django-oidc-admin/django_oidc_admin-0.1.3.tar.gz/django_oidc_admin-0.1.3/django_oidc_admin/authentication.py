import logging

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from mozilla_django_oidc.views import OIDCAuthenticationCallbackView
from django.utils.translation import gettext as _
from django.db import IntegrityError

logger = logging.getLogger(__name__)

class DjangoOIDCAdminBackend(OIDCAuthenticationBackend):
    """
    Custom OIDC backend to manage the user creation and filtering.
    """

    def create_user(self, claims):
        """
        Create a user with the given claims.
        """
        email = claims.get("email")
        if not email:
            return None  # Refuse user creation if no email is provided

        # User is inactive by default
        username = claims.get("preferred_username", email)
        name = claims.get("name", "")
        given_name = claims.get("given_name", "")
        try:
            user = get_user_model().objects.create_user(
                username=username, first_name=given_name, last_name=name, email=email, is_active=False
            )
        except IntegrityError as e:
            logger.warning(f"User can not be created with username {username} -> {e}")
            # If duplicated username, fallback to the email as username
            user = get_user_model().objects.create_user(
                username=email, first_name=given_name, last_name=name, email=email, is_active=False
            )

        # Add user to Users groups
        if settings.DOIDCADMIN_NEW_USER_GROUP_NAME is not None:
            group, created = Group.objects.get_or_create(name=settings.DOIDCADMIN_NEW_USER_GROUP_NAME)
            user.groups.add(group)

        return user

    def filter_users_by_claims(self, claims):
        """
        Return all users matching the given claims.
        """
        email = claims.get("email")
        if not email:
            return self.UserModel.objects.none()
        return self.UserModel.objects.filter(email=email)


class DjangoOIDCAdminCallbackView(OIDCAuthenticationCallbackView):
    """
    Custom OIDC callback view to manage the user login failure and redirection to the login page.

    We do not authenticate the user right away, we let the admin user validate the account first.
    As the user is not active by default, the authentication will fail and the user
    will be redirected to the login page.

    """

    def login_failure(self):
        """
        Override the default login_failure method to ovoid the unsafe redirect admin page error
        """
        return redirect(self.failure_url)

    def get(self, request):
        """ """
        response = super().get(request)

        # The user account needs to be validated by an admin before he/she can log in
        if self.user and not self.user.is_active:
            messages.warning(
                request,
                _("Your account has been created and is pending validation. Please wait for an administrator to validate your account."),
            )

        return response
