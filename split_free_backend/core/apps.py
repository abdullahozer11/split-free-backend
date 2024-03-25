# Copyright (c) 2023 SplitFree Org.

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "split_free_backend.core"

    def ready(self):
        import split_free_backend.core.signals  # noqa
