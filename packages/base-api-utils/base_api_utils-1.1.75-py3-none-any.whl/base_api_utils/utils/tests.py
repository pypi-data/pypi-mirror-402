from django.conf import settings

from . import async_task


@async_task(max_retries=0)
def always_fails_task(self, test_id, reason="Test failure"):
    raise ValueError(f"Test {test_id} failed: {reason}")

def celery_is_correctly_configured():
    if getattr(settings, 'CELERY_RESULT_BACKEND', None) != 'django-db':
        return False

    if 'django_celery_results' not in settings.INSTALLED_APPS:
        return False

    return True