from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from django.conf import settings
from django.http import HttpRequest
from qstash import Receiver

from django_qstash.db.models import TaskStatus

from . import utils
from .exceptions import PayloadError
from .exceptions import SignatureError
from .exceptions import TaskError
from .results.services import store_task_result

logger = logging.getLogger(__name__)


@dataclass
class TaskPayload:
    function: str
    module: str
    args: list
    kwargs: dict
    task_name: str
    function_path: str

    @classmethod
    def from_dict(cls, data: dict) -> TaskPayload:
        """Create TaskPayload from dictionary."""
        is_valid, error = utils.validate_task_payload(data)
        if not is_valid:
            raise PayloadError(error)

        function_path = f"{data['module']}.{data['function']}"
        return cls(
            function=data["function"],
            module=data["module"],
            args=data["args"],
            kwargs=data["kwargs"],
            task_name=data.get("task_name", function_path),
            function_path=function_path,
        )


class QStashWebhook:
    def __init__(self):
        self.receiver = Receiver(
            current_signing_key=settings.QSTASH_CURRENT_SIGNING_KEY,
            next_signing_key=settings.QSTASH_NEXT_SIGNING_KEY,
        )
        self.force_https = getattr(settings, "DJANGO_QSTASH_FORCE_HTTPS", True)

    def verify_signature(self, body: str, signature: str, url: str) -> None:
        """Verify QStash signature."""
        if not signature:
            raise SignatureError("Missing Upstash-Signature header")

        if self.force_https and not url.startswith("https://"):
            url = url.replace("http://", "https://")

        try:
            self.receiver.verify(body=body, signature=signature, url=url)
        except Exception as e:
            raise SignatureError(f"Invalid signature: {e}")

    def parse_payload(self, body: str) -> TaskPayload:
        """Parse and validate webhook payload."""
        try:
            data = json.loads(body)
            return TaskPayload.from_dict(data)
        except json.JSONDecodeError as e:
            raise PayloadError(f"Invalid JSON payload: {e}")

    def execute_task(self, payload: TaskPayload) -> Any:
        """Import and execute the task function."""
        try:
            task_func = utils.import_string(payload.function_path)
        except ImportError as e:
            raise TaskError(f"Could not import task function: {e}")

        try:
            if callable(task_func) and hasattr(task_func, "actual_func"):
                return task_func.actual_func(*payload.args, **payload.kwargs)
            return task_func(*payload.args, **payload.kwargs)
        except Exception as e:
            raise TaskError(f"Task execution failed: {e}")

    def handle_request(self, request: HttpRequest) -> tuple[dict, int]:
        """Process webhook request and return response data and status code."""
        payload = None
        task_id = request.headers.get("Upstash-Message-Id")

        try:
            body = request.body.decode()
            self.verify_signature(
                body=body,
                signature=request.headers.get("Upstash-Signature"),
                url=request.build_absolute_uri(),
            )

            payload = self.parse_payload(body)
            result = self.execute_task(payload)
            store_task_result(
                task_id=task_id,
                task_name=payload.task_name,
                status=TaskStatus.SUCCESS,
                result=result,
                args=payload.args,
                kwargs=payload.kwargs,
                function_path=payload.function_path,
            )

            return {
                "status": "success",
                "task_name": payload.task_name,
                "result": result if result is not None else "null",
            }, 200

        except (SignatureError, PayloadError) as e:
            logger.exception("Authentication error: %s", str(e))
            return {
                "status": "error",
                "error_type": e.__class__.__name__,
                "error": str(e),
                "task_name": getattr(payload, "task_name", None),
            }, 400

        except TaskError as e:
            logger.exception("Task execution error: %s", str(e))
            store_task_result(
                task_id=task_id,
                task_name=payload.task_name,
                status=TaskStatus.EXECUTION_ERROR,
                traceback=str(e),
                args=payload.args,
                kwargs=payload.kwargs,
                function_path=payload.function_path,
            )
            return {
                "status": "error",
                "error_type": e.__class__.__name__,
                "error": str(e),
                "task_name": payload.task_name,
            }, 422

        except Exception as e:
            logger.exception("Unexpected error in webhook handler: %s", str(e))
            if payload:  # Store unexpected errors only if payload was parsed
                store_task_result(
                    task_id=task_id,
                    task_name=payload.task_name,
                    status=TaskStatus.INTERNAL_ERROR,
                    traceback=str(e),
                    args=payload.args,
                    kwargs=payload.kwargs,
                    function_path=payload.function_path,
                )
            return {
                "status": "error",
                "error_type": "InternalServerError",
                "error": "An unexpected error occurred",
                "task_name": getattr(payload, "task_name", None),
            }, 500
