from __future__ import annotations

import warnings

from django.conf import settings

QSTASH_TOKEN = getattr(settings, "QSTASH_TOKEN", None)
DJANGO_QSTASH_DOMAIN = getattr(settings, "DJANGO_QSTASH_DOMAIN", None)
DJANGO_QSTASH_WEBHOOK_PATH = getattr(
    settings, "DJANGO_QSTASH_WEBHOOK_PATH", "/qstash/webhook/"
)
if not QSTASH_TOKEN or not DJANGO_QSTASH_DOMAIN:
    warnings.warn(
        "DJANGO_SETTINGS_MODULE (settings.py required) requires QSTASH_TOKEN and DJANGO_QSTASH_DOMAIN should be set for QStash functionality",
        RuntimeWarning,
        stacklevel=2,
    )
