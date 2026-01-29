from django import template
from django.urls import reverse

from ..settings import OIDCADMIN_USER_LIST_URL_NAME

register = template.Library()


@register.simple_tag
def user_list_url():
    return reverse(OIDCADMIN_USER_LIST_URL_NAME)
