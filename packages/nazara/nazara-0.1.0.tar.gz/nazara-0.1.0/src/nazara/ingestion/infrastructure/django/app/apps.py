from django.apps import AppConfig


class NazaraIngestionConfig(AppConfig):
    """Django AppConfig for Nazara Ingestion context."""

    name = "nazara.ingestion.infrastructure.django.app"
    label = "nazara_ingestion"
    verbose_name = "Nazara - Ingestion"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        from nazara.containers import _container, init_container

        # Only initialize once (first app to load does it)
        if _container is None:
            init_container()
