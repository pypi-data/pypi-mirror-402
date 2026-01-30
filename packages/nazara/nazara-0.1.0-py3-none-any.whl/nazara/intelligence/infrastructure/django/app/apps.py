from django.apps import AppConfig


class NazaraIntelligenceConfig(AppConfig):
    name = "nazara.intelligence.infrastructure.django.app"
    label = "nazara_intelligence"
    verbose_name = "Nazara - Intelligence"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        from nazara.intelligence.application import event_handlers  # noqa: F401
