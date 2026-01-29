from __future__ import annotations

import pytest

from django_qstash.exceptions import PayloadError
from django_qstash.exceptions import SignatureError
from django_qstash.exceptions import TaskError
from django_qstash.exceptions import WebhookError


def test_webhook_error():
    """Test that WebhookError can be raised and is an Exception"""
    with pytest.raises(WebhookError):
        raise WebhookError("Test webhook error")


def test_signature_error():
    """Test that SignatureError can be raised and is a WebhookError"""
    with pytest.raises(SignatureError):
        raise SignatureError("Invalid signature")

    # Verify inheritance
    assert issubclass(SignatureError, WebhookError)


def test_payload_error():
    """Test that PayloadError can be raised and is a WebhookError"""
    with pytest.raises(PayloadError):
        raise PayloadError("Invalid payload")

    # Verify inheritance
    assert issubclass(PayloadError, WebhookError)


def test_task_error():
    """Test that TaskError can be raised and is a WebhookError"""
    with pytest.raises(TaskError):
        raise TaskError("Task execution failed")

    # Verify inheritance
    assert issubclass(TaskError, WebhookError)


def test_error_messages():
    """Test that error messages are properly stored"""
    message = "Custom error message"

    try:
        raise WebhookError(message)
    except WebhookError as e:
        assert str(e) == message

    try:
        raise SignatureError(message)
    except SignatureError as e:
        assert str(e) == message
