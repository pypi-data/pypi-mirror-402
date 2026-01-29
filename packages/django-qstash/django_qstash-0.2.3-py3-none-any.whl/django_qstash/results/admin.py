from __future__ import annotations

from django.contrib import admin

from .models import TaskResult


@admin.register(TaskResult)
class TaskResultAdmin(admin.ModelAdmin):
    readonly_fields = [
        "task_name",
        "status",
        "date_done",
        "result",
        "traceback",
        "args",
        "kwargs",
        "task_id",
        "date_created",
        "function_path",
    ]
    search_fields = ["task_name", "task_id", "function_path"]
    list_display = ["task_name", "function_path", "status", "date_done"]
    list_filter = ["status", "date_done"]
