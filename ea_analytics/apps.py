from django.apps import AppConfig


class EaAnalyticsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ea_analytics"
    verbose_name = "EA Analytics"

    def ready(self):
        import ea_analytics.signals  # noqa: F401 – register signals
