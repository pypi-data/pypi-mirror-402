from django.http import JsonResponse


def health(request):
    return JsonResponse({"status": "healthy"})


def ready(request):
    checks = {
        "database": _check_database(),
        "cache": _check_cache(),
    }

    all_healthy = all(c["status"] == "ok" for c in checks.values())
    status_code = 200 if all_healthy else 503

    return JsonResponse(
        {"status": "ready" if all_healthy else "not_ready", "checks": checks},
        status=status_code,
    )


def _check_database() -> dict:
    from django.db import connection

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def _check_cache() -> dict:
    from django.core.cache import cache

    try:
        cache.set("health_check", "ok", timeout=1)
        value = cache.get("health_check")
        if value == "ok":
            return {"status": "ok"}
        return {"status": "error", "error": "Cache read/write failed"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
