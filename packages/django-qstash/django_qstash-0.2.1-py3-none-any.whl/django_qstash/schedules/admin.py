from __future__ import annotations

from django.contrib import admin

from django_qstash.schedules import services
from django_qstash.schedules.forms import TaskScheduleForm
from django_qstash.schedules.models import TaskSchedule


@admin.register(TaskSchedule)
class TaskScheduleAdmin(admin.ModelAdmin):
    list_display = ["schedule_id", "task_name"]
    readonly_fields = [
        "schedule_id",
        "task_name",
        "get_qstash_schedule_details",
        "paused_at",
        "resumed_at",
        "active_at",
    ]
    form = TaskScheduleForm

    fieldsets = [
        (
            "Name",
            {
                "fields": ["name", "schedule_id", "is_active"],
            },
        ),
        (
            "Task Selection",
            {
                "fields": ["task", "task_name"],
            },
        ),
        (
            "Arguments",
            {
                "fields": ["args", "kwargs"],
            },
        ),
        (
            "Schedule",
            {
                "fields": ["cron", "retries", "timeout"],
            },
        ),
        (
            "QStash Metadata",
            {
                "fields": [
                    "paused_at",
                    "resumed_at",
                    "active_at",
                    "get_qstash_schedule_details",
                ],
                "classes": ["collapse"],
            },
        ),
    ]

    @admin.display(description="Raw")
    def get_qstash_schedule_details(self, obj: TaskSchedule) -> dict:
        if not obj.schedule_id:
            return "No schedule ID yet"
        return services.get_task_schedule_from_qstash(obj, as_dict=True)
