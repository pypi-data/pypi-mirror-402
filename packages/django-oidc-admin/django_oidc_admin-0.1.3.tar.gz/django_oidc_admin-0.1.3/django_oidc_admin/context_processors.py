from django.contrib.auth import get_user_model


def admin_navbar(request):
    """Add the number of pending SSO users to the available context in templates"""
    if request.user.is_staff:
        return {
            "pending_sso_users": get_user_model().objects.filter(is_active=False).count(),
        }
    return {}
