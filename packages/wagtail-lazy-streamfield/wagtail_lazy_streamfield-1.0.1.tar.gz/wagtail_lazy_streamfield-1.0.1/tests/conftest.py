import django
from django.conf import settings


def pytest_configure() -> None:
    """Configure Django settings for tests."""
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
                "wagtail",
                "wagtail.documents",
                "wagtail.images",
                "taggit",
            ],
            USE_TZ=True,
            SECRET_KEY="test-secret-key",
        )
        django.setup()
