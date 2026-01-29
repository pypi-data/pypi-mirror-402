from __future__ import annotations

from django.core.management.base import BaseCommand

from django_qstash.discovery.utils import discover_tasks


class Command(BaseCommand):
    help = "View all available tasks"

    def add_arguments(self, parser):
        parser.add_argument(
            "--locations",
            action="store_true",
            help="Only show task paths",
        )

    def handle(self, *args, **options):
        locations_only = options["locations"] or False
        self.stdout.write("Available tasks:")
        discover_tasks.cache_clear()
        if locations_only:
            tasks = discover_tasks(locations_only=locations_only)
            for task in tasks:
                self.stdout.write(f"\t- {self.style.SQL_FIELD(task)}")
        else:
            tasks = discover_tasks(locations_only=False)
            for task in tasks:
                name = task["name"]
                field_label = task["field_label"]
                location = task["location"]
                self.stdout.write(
                    f"  Name: {self.style.SQL_FIELD(name)}\n"
                    f"  Location: {self.style.SQL_FIELD(location)}\n"
                    f"  Field Label: {self.style.SQL_FIELD(field_label)}"
                )
                self.stdout.write("")
