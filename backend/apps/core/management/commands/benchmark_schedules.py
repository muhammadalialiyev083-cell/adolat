import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from apps.engine.experiments import run_experiment


class Command(BaseCommand):
    help = "Takrorlanadigan sun’iy usul taqqoslash tajribasi; bazani o‘zgartirmaydi."

    def add_arguments(self, parser):
        parser.add_argument("--repeats", type=int, default=10)
        parser.add_argument("--output")

    def handle(self, *args, **options):
        if not 1 <= options["repeats"] <= 1000:
            raise CommandError("Takrorlar soni 1..1000 bo‘lsin.")
        text = json.dumps(run_experiment(options["repeats"]), ensure_ascii=False, indent=2)
        if options["output"]:
            Path(options["output"]).write_text(text, encoding="utf-8")
            self.stdout.write("Sun’iy tajriba natijasi saqlandi.")
        else:
            self.stdout.write(text)
