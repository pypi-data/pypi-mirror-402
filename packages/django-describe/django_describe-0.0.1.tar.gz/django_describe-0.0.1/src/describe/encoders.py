from pathlib import PosixPath

from django.core.serializers.json import DjangoJSONEncoder


class DescribeJSONEncoder(DjangoJSONEncoder):

    def default(self, o):
        if isinstance(o, PosixPath):
            return str(o)
        return super().default(o)
