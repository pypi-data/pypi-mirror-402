from django.conf import settings

DOIDCADMIN_NEW_USER_GROUP_NAME = getattr(settings, "DOIDCADMIN_NEW_USER_GROUP_NAME", None)
OIDCADMIN_USER_LIST_URL_NAME = getattr(settings, 'OIDCADMIN_USER_LIST_URL_NAME', 'admin:auth_user_changelist')
