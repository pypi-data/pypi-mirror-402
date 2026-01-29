"""Django settings for tests."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production

SECRET_KEY = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'

INTERNAL_IPS = ['127.0.0.1']

LOGGING_CONFIG = None   # avoids spurious output in tests


# Application definition

INSTALLED_APPS = [
    "django_oidc_admin",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tests',
]


MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

AUTHENTICATION_BACKENDS = (
    "django_oidc_admin.authentication.DjangoOIDCAdminBackend",  # Authentification OIDC
    "django.contrib.auth.backends.ModelBackend",  # Classic authentification
)

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django_oidc_admin.context_processors.admin_navbar"
            ],
        },
    },
]

ROOT_URLCONF = 'tests.urls'

# Cache and database
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
    'second': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'DMOCTestDatabase',

    }
}

STATIC_URL = '/static/'

OIDC_RP_CLIENT_ID = "tests"
OIDC_RP_CLIENT_SECRET = "tests"
OIDC_RP_SCOPES = "openid email profile"
OIDC_OP_AUTHORIZATION_ENDPOINT = "tests"
OIDC_OP_TOKEN_ENDPOINT = "tests"
OIDC_OP_USER_ENDPOINT = "tests"
OIDC_OP_JWKS_ENDPOINT = "tests"
OIDC_RP_SIGN_ALGO = "RS256"
DMOC_NEW_USER_GROUP_NAME = "Users"
# LOGIN_REDIRECT_URL = "admin:index"
# LOGIN_REDIRECT_URL_FAILURE = "admin:index"
OIDC_CALLBACK_CLASS = "django_oidc_admin.authentication.DjangoOIDCAdminCallbackView"
