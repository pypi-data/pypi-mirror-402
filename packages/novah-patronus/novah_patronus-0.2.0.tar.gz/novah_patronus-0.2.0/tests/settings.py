"""
Django settings for mypy and pytest.

This minimal settings module is used by:
- mypy's django-stubs plugin for type checking
- pytest-django for running tests

It provides just enough configuration for the tools to work without
requiring a full Django project setup.
"""

SECRET_KEY = "test-secret-key-not-for-production"

DEBUG = True

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "rest_framework",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

ROOT_URLCONF = ""

USE_TZ = True

PATRONUS: dict[str, object] = {}
