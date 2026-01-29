from __future__ import annotations

from django.urls import path

from django_qstash.views import qstash_webhook_view

urlpatterns = [
    path("", qstash_webhook_view),
]
