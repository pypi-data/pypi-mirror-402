import json

from contextlib import contextmanager

from django.core.management.base import BaseCommand, CommandError

from describe.encoders import DescribeJSONEncoder
from describe.utils import get_models, get_settings, get_apps


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

    @staticmethod
    def get_metadata(values):
        get_apps(values, exclude_site_packages=True)
        get_models(values, exclude_site_packages=True)
        get_settings(values)

    def handle(self, *args, **options):
        output = options["output"]
        metadata = {}

        try:
            self.get_metadata(metadata)
            with self.output_stream(output) as out:
                out.write(json.dumps(metadata, cls=DescribeJSONEncoder, indent=4))
        except Exception as e:
            raise CommandError("Unable to generate metadata for project: %s" % e)
