"""
Django settings for swiftapi tests.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = "test-secret-key-do-not-use-in-production"
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

USE_TZ = True

# SwiftAPI settings
SWIFTAPI = {
    "PAGE_SIZE": 25,
    "MAX_PAGE_SIZE": 100,
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "swiftapi.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "swiftapi.permissions.AllowAny",
    ],
}
