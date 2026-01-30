import hashlib
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser


def get_temp_dir() -> Path:
    match sys.platform:
        case "win32":
            return Path(os.path.expandvars("%temp%"))
        case "darwin":
            return Path("/var/tmp")
        case _:
            return Path("/tmp")


def get_file_name() -> Path:
    project = Path(settings.BASE_DIR).name
    return get_temp_dir() / f"uptime.{project}"


class Command(BaseCommand):
    help = "Calculate uptime"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("-s", "--start", action="store_true")
        parser.add_argument("--filename", action="store_true")

    def get_uptime(self, start: bool = False, verbosity: int = 1) -> str:
        file = get_file_name()
        if not file.exists() or start:
            file.touch()
            if verbosity > 1:
                self.stdout.write(f"{'Recreated' if start else 'Created'} {file}\n")
        elif verbosity > 1:
            self.stdout.write(f"Checked {file}\n")

        started_at = file.stat().st_mtime
        return str(datetime.now() - datetime.fromtimestamp(started_at))

    def handle(self, *args, **options) -> None:
        filename_only = options.get("filename", False)
        if filename_only:
            self.stdout.write(f"{get_file_name()}\n")
            return

        start = options.get("start", False)
        verbosity = options.get("verbosity", 1)
        self.stdout.write(f"{self.get_uptime(start, verbosity)}\n")
