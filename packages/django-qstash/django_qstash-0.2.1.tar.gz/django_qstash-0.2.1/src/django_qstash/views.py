from __future__ import annotations

import json

from django.http import HttpRequest
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .handlers import QStashWebhook


@csrf_exempt
@require_http_methods(["POST"])
def qstash_webhook_view(request: HttpRequest) -> HttpResponse:
    """Handle QStash webhook requests."""
    webhook = QStashWebhook()
    response_data, status_code = webhook.handle_request(request)
    return HttpResponse(
        json.dumps(response_data), status=status_code, content_type="application/json"
    )
