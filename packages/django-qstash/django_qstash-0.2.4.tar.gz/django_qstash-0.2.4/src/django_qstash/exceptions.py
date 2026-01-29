from __future__ import annotations


class WebhookError(Exception):
    """Base exception for webhook handling errors."""

    pass


class SignatureError(WebhookError):
    """Invalid or missing signature."""

    pass


class PayloadError(WebhookError):
    """Invalid payload structure or content."""

    pass


class TaskError(WebhookError):
    """Error in task execution."""

    pass
