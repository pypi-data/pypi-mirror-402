from django.apps import AppConfig


class NazaraSignalsConfig(AppConfig):
    """Configuration for the Nazara Signals app."""

    name = "nazara.signals.infrastructure.django.app"
    label = "nazara_signals"
    verbose_name = "Nazara - Signals"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        """Ensure DI container is initialized."""
        from nazara.containers import _container, init_container

        # Initialize if not already done by another app
        if _container is None:
            init_container()
