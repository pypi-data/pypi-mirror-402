import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sandbox.settings")

app = Celery("sandbox")
app.config_from_object("django.conf:settings", namespace="CELERY")
# Autodiscover tasks from installed apps
app.autodiscover_tasks()

# Explicitly import tasks from DDD infrastructure modules
# (These are outside Django app directories, so autodiscover won't find them)
# Import triggers registration with the celery app
import nazara.ingestion.infrastructure.messaging.tasks  # noqa: F401, E402
import nazara.intelligence.infrastructure.messaging.tasks  # noqa: F401, E402
import nazara.shared.event_bus.tasks  # noqa: F401, E402
import nazara.signals.infrastructure.messaging.tasks  # noqa: F401, E402
