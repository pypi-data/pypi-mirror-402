from __future__ import annotations

from unittest.mock import patch

import pytest

from django_qstash.callbacks import get_callback_url


@pytest.mark.parametrize(
    "domain,webhook_path,expected",
    [
        # Domain without protocol
        (
            "example.com",
            "webhook",
            "https://example.com/webhook/",
        ),
        # Domain with http protocol
        (
            "http://example.com",
            "webhook",
            "http://example.com/webhook/",
        ),
        # Domain with https protocol
        (
            "https://example.com",
            "webhook",
            "https://example.com/webhook/",
        ),
        # Domain with trailing slash
        (
            "example.com/",
            "webhook",
            "https://example.com/webhook/",
        ),
        # Webhook path with leading slash
        (
            "example.com",
            "/webhook",
            "https://example.com/webhook/",
        ),
        # Webhook path with trailing slash
        (
            "example.com",
            "webhook/",
            "https://example.com/webhook/",
        ),
        # Complex path
        (
            "example.com",
            "api/v1/webhook",
            "https://example.com/api/v1/webhook/",
        ),
    ],
)
def test_get_callback_url(domain, webhook_path, expected):
    with (
        patch("django_qstash.callbacks.DJANGO_QSTASH_DOMAIN", domain),
        patch("django_qstash.callbacks.DJANGO_QSTASH_WEBHOOK_PATH", webhook_path),
    ):
        assert get_callback_url() == expected
