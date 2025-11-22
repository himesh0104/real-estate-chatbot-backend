from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from api.models import RealEstateData
from api.utils.data_processor import RealEstateDataProcessor


class Command(BaseCommand):
    help = "Import real estate data from the configured Excel/CSV file or Google Sheet into the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            dest="file_path",
            help="Optional path to a local Excel/CSV file. Defaults to settings.EXCEL_FILE_PATH.",
        )
        parser.add_argument(
            "--url",
            dest="data_url",
            help="Optional Google Sheet/CSV URL. Defaults to settings.REAL_ESTATE_DATA_URL.",
        )
        parser.add_argument(
            "--truncate",
            action="store_true",
            help="Remove existing RealEstateData records before importing.",
        )

    def handle(self, *args, **options):
        file_path = options.get("file_path") or settings.EXCEL_FILE_PATH
        data_url = options.get("data_url") or getattr(settings, "REAL_ESTATE_DATA_URL", None)

        processor = RealEstateDataProcessor(
            excel_file_path=file_path,
            data_url=data_url,
            prefer_database=False,
        )

        df = processor.df
        if df is None or df.empty:
            raise CommandError("No rows available to import. Verify the provided file path or URL.")

        if options["truncate"]:
            deleted, _ = RealEstateData.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Removed {deleted} existing rows."))

        model_fields = RealEstateDataProcessor.COLUMN_MAP.values()
        payloads = []
        for row in df.to_dict(orient="records"):
            payload = {field: row.get(field) for field in model_fields}
            payloads.append(RealEstateData(**payload))

        RealEstateData.objects.bulk_create(payloads, batch_size=500)
        self.stdout.write(self.style.SUCCESS(f"Imported {len(payloads)} real estate rows."))
