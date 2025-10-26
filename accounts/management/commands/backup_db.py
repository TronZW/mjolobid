import os
import gzip
import shutil
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Backup SQLite database to a timestamped file with optional compression and rotation."

    def add_arguments(self, parser):
        parser.add_argument(
            "--keep",
            type=int,
            default=7,
            help="Number of most recent backups to keep (older ones are deleted).",
        )
        parser.add_argument(
            "--no-compress",
            action="store_true",
            help="Do not gzip the backup file.",
        )
        parser.add_argument(
            "--backup-dir",
            type=str,
            default=None,
            help="Directory to store backups. Defaults to the database directory / 'backups'.",
        )

    def handle(self, *args, **options):
        default_db = settings.DATABASES.get("default", {})
        engine = default_db.get("ENGINE", "")

        if engine != "django.db.backends.sqlite3":
            self.stdout.write(self.style.WARNING("Skipping backup: not using SQLite backend."))
            return

        db_path = Path(default_db.get("NAME", "")).expanduser()
        if not db_path:
            self.stdout.write(self.style.ERROR("No SQLite database path found."))
            return

        if not db_path.exists():
            self.stdout.write(self.style.WARNING(f"Skipping backup: database file not found at {db_path}."))
            return

        backup_root = (
            Path(options["backup_dir"]).expanduser()
            if options.get("backup_dir")
            else db_path.parent / "backups"
        )
        backup_root.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        base_name = f"db-{timestamp}.sqlite3"
        dest_path = backup_root / base_name

        try:
            # Copy database file
            shutil.copy2(str(db_path), str(dest_path))
            self.stdout.write(self.style.SUCCESS(f"Created backup: {dest_path}"))

            # Optionally compress
            if not options.get("no_compress"):
                gz_path = f"{dest_path}.gz"
                with open(dest_path, "rb") as f_in, gzip.open(gz_path, "wb", compresslevel=6) as f_out:
                    shutil.copyfileobj(f_in, f_out)
                os.remove(dest_path)
                dest_path = Path(gz_path)
                self.stdout.write(self.style.SUCCESS(f"Compressed backup: {dest_path}"))

            # Rotation
            keep = int(options.get("keep") or 7)
            backups = sorted(backup_root.glob("db-*.sqlite3*"), key=lambda p: p.stat().st_mtime, reverse=True)
            for old in backups[keep:]:
                try:
                    old.unlink(missing_ok=True)
                    self.stdout.write(f"Removed old backup: {old}")
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Could not remove {old}: {e}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Backup failed: {e}"))
            raise


