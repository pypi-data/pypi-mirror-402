from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from django.test import Client


@pytest.mark.django_db
class TestQStashWebhook:
    def setup_method(self):
        self.client = Client()
        self.url = "/qstash/webhook/"

    @patch("django_qstash.views.QStashWebhook")
    def test_valid_webhook_request(self, mock_webhook_class):
        """Test webhook with valid signature and payload"""
        # Setup mock webhook instance
        mock_webhook = mock_webhook_class.return_value
        mock_webhook.handle_request.return_value = ({"status": "success"}, 200)

        payload = {
            "function": "sample_task",
            "module": "tests.test_tasks",
            "args": [2, 3],
            "kwargs": {},
            "task_name": "test_task",
        }

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
            headers={"upstash-signature": "mock-signature"},
        )

        # Verify response
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["status"] == "success"

        # Verify webhook was called correctly
        mock_webhook.handle_request.assert_called_once()

    @patch("django_qstash.views.QStashWebhook")
    def test_invalid_request(self, mock_webhook_class):
        """Test webhook with invalid request"""
        # Setup mock webhook instance
        mock_webhook = mock_webhook_class.return_value
        mock_webhook.handle_request.return_value = ({"error": "Invalid request"}, 400)

        response = self.client.post(
            self.url,
            data="invalid json",
            content_type="application/json",
            headers={"upstash-signature": "mock-signature"},
        )

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert "error" in response_data
