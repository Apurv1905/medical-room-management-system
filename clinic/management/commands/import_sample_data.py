import json
from django.apps import apps
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.core import serializers
from django.db import transaction

from clinic.models import Patient


class Command(BaseCommand):
    help = "Import fictional demo records from the sample data fixture."

    def handle(self, *args, **options):
        fixture_path = (
            Path(__file__).resolve().parents[2]
            / "fixtures"
            / "demo_sample_data.json"
        )

        if not fixture_path.exists():
            raise CommandError(
                f"Sample data fixture not found: {fixture_path}"
            )

        # Avoid accidentally importing the same records twice
        # or mixing them with records already on the server.

        clinic_models = apps.get_app_config("clinic").get_models()

        if any(model.objects.exists() for model in clinic_models):
           self.stdout.write(
             self.style.WARNING(
               "Clinic records already exist. Import skipped."
        )
    )
        return
        try:
            with fixture_path.open("r", encoding="utf-8") as file:
                fixture_data = json.load(file)

            # The local user account is not transferred.
            # Set MedicineStockMovement.created_by to NULL so that
            # stock movements do not depend on a local user ID.
            for item in fixture_data:
                if item.get("model") == "clinic.medicinestockmovement":
                    item.setdefault("fields", {})["created_by"] = None

            fixture_json = json.dumps(fixture_data)

            with transaction.atomic():
                imported_count = 0

                for obj in serializers.deserialize("json", fixture_json):
                    obj.save()
                    imported_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully imported {imported_count} demo records."
                )
            )

        except Exception as error:
            raise CommandError(
                f"Import failed. No partial import was retained. Details: {error}"
            ) from error