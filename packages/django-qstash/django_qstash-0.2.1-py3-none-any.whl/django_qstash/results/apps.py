from __future__ import annotations

from django.apps import AppConfig


class ResultsConfig(AppConfig):
    name = "django_qstash.results"
    label = "django_qstash_results"
    verbose_name = "django_qstash_results"
    default_auto_field = "django.db.models.BigAutoField"
