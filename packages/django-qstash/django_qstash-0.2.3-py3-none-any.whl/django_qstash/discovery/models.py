from __future__ import annotations

from django.db import models

from django_qstash.discovery.fields import TaskChoiceField


class TaskField(models.CharField):
    """
    A model field for storing QStash task references
    """

    def __init__(self, *args, **kwargs):
        # Set a reasonable max_length for task names if not provided
        if "max_length" not in kwargs:
            kwargs["max_length"] = 255
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        # Use our custom form field
        defaults = {
            "form_class": TaskChoiceField,
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)
