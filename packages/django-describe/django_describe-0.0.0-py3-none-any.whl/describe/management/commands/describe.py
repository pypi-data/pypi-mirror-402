import sys

from contextlib import contextmanager

from django.core.management.base import BaseCommand, CommandError



class Command(BaseCommand):
    help = "Generate the metadata that describes a Django project"

    def add_arguments(self, parser):
        parser.add_argument(
            "-o", "--output", help="Specifies file to which the output is written."
        )

    @contextmanager
    def output_stream(self, filename=None):
        if filename:
            f = open(filename, "w")
            yield f
            f.close()
        else:
            yield self.stdout

    def handle(self, *args, **options):
        output = options["output"] or self.stdout

        try:
            with self.output_stream(output) as out:
                out.write("{}")

        except Exception as e:
            raise CommandError("Unable to generate metadata for project: %s" % e)
