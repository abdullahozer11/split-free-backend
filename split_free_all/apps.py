from django.apps import AppConfig


class SplitFreeAllConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "split_free_all"

    def ready(self):
        import split_free_all.signals  # noqa
