from sandbox.settings import *  # noqa: F401, F403

# Test overrides
SECRET_KEY = "test-secret-key-not-for-production"
DEBUG = True

# Test database
DATABASES["default"]["NAME"] = "nazara_test"  # noqa: F405

# In-memory cache (no Redis needed)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Celery: synchronous execution for tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"

# Disable scheduled tasks in tests
CELERY_BEAT_SCHEDULE = {}

# Synchronous event bus for tests
EVENT_BUS_DRIVER = "in-memory"
