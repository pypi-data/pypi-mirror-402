from django.urls import path, include

urlpatterns = [
    # Use all urls of mozilla_django_oidc
    path("", include("mozilla_django_oidc.urls")),
]
