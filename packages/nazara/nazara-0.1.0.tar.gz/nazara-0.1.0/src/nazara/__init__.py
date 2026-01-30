from __future__ import annotations

__version__ = "0.1.0"

NAZARA_APPS = [
    "nazara.signals.infrastructure.django.app",
    "nazara.ingestion.infrastructure.django.app",
    "nazara.intelligence.infrastructure.django.app",
]

NAZARA_REQUIRED_APPS = [
    "django_select2",
    "django_json_widget",
    "django_admin_inline_paginator_plus",
    "django_celery_beat",
    "django_celery_results",
    *NAZARA_APPS,
]


def get_celery_beat_schedule() -> dict:
    from celery.schedules import crontab

    return {
        "nazara-poll-ingestors": {
            "task": "nazara.ingestion.infrastructure.messaging.tasks.poll_all_ingestors_task",
            "schedule": 60.0,
            "options": {"queue": "celery"},
        },
        "nazara-cleanup-stale-data": {
            "task": "nazara.signals.infrastructure.messaging.tasks.cleanup_all_stale_data_task",
            "schedule": crontab(hour=3, minute=0),
            "options": {"queue": "celery"},
        },
        "nazara-mark-stale-resolved": {
            "task": "nazara.signals.infrastructure.messaging.tasks.mark_stale_issues_resolved_task",
            "schedule": crontab(hour=4, minute=0),
            "options": {"queue": "celery"},
        },
    }


def configure(settings: dict, **overrides) -> None:
    """
    Configure Django settings for Nazara.

    Adds required INSTALLED_APPS, Celery configuration, and Nazara defaults.
    Call this after defining your base Django settings.

    Usage:
        import nazara
        nazara.configure(globals())

    With overrides:
        nazara.configure(globals(), EVENT_BUS_DRIVER="in-memory")

    Args:
        settings: The settings dict (typically globals() from settings.py)
        **overrides: Override any Nazara default settings
    """
    apps = list(settings.get("INSTALLED_APPS", []))
    for app in NAZARA_REQUIRED_APPS:
        if app not in apps:
            apps.append(app)
    settings["INSTALLED_APPS"] = apps

    settings.setdefault("CELERY_RESULT_BACKEND", "django-db")
    settings.setdefault("CELERY_BEAT_SCHEDULER", "django_celery_beat.schedulers:DatabaseScheduler")
    settings.setdefault("CELERY_TASK_TRACK_STARTED", True)
    settings.setdefault("CELERY_TASK_TIME_LIMIT", 30 * 60)
    settings.setdefault("CELERY_TASK_ALWAYS_EAGER", False)
    settings.setdefault("CELERY_TASK_EAGER_PROPAGATES", False)

    beat_schedule = settings.get("CELERY_BEAT_SCHEDULE", {})
    beat_schedule.update(get_celery_beat_schedule())
    settings["CELERY_BEAT_SCHEDULE"] = beat_schedule

    settings.setdefault("EVENT_BUS_DRIVER", "celery")
    settings.setdefault("NAZARA_SECRET_RESOLVER_TYPE", "env")
    settings.setdefault("NAZARA_SECRET_ENV_PREFIX", "NAZARA_")
    settings.setdefault("NAZARA_SECRETS_FILE", None)

    for key, value in overrides.items():
        settings[key] = value
