# django-describe
django-describe generates a report on the run-time configuration of a Django site after 
everything has been loaded or created and initialised- generating lists of installed apps, 
models registered with the Django Admin, urls served, etc. The reports are generated in 
json format. 

The reports are the metadata for a site. You can use the reports for anything, but the 
reason django-describe was created was to feed the information into an LLM to generate 
tests.

# Usage
Generate a complete report using the following:

```shell
python manage.py describe
```

Reports, by default, are written to the console, but you can save them to a file either by 
redirecting the output, or using the `--output` option:
```
python manage,py describe --output metadata/description.json
```

## Output
django-describe generates the report in JSON format:

```json
{
    "apps": [
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "describe"
    ],
    "models": [
        "admin.logentry",
        "auth.permission",
        "auth.group",
        "auth.user",
        "contenttypes.contenttype",
        "sessions.session"
    ],
    "settings": {
        "ABSOLUTE_URL_OVERRIDES": {},
        "ADMINS": [],
        "ALLOWED_HOSTS": [],
        "APPEND_SLASH": true,
        "AUTHENTICATION_BACKENDS": [
            "django.contrib.auth.backends.ModelBackend"
        ],
        ...
    }
}
```
Note: The report normally does not include information from dependencies. They
were only included as the django-describe app does not include any models.

## Install

You can use either [pip](https://pip.pypa.io/en/stable/) or [uv](https://docs.astral.sh/uv/)
to download the [package](https://pypi.org/project/django-describe/) from PyPI and
install it into a virtualenv:

```shell
pip install django-describe
```

or:

```shell
uv add django-describe
```

Update `INSTALLED_APPS` in your Django setting:

```python
INSTALLED_APPS = [
    ...
    "describe",
]
```

## Demo

If you check out the code from the repository there is a fully functioning,
but minimal Django site, which you can used to see how the management command
works.

```shell
git clone git@github.com:StuartMacKay/django-describe.git
cd django-describe
```

Create the virtual environment:
```shell
uv venv
```

Activate it:
```shell
source .venv/bin/activate
```

Install the requirements:
```shell
uv sync
```

Run the database migrations:
```shell
python manage.py migrate
```

Now, run the management command to generate the report:

```shell
python manage.py describe --output metadata.json
```

## Project Information

* Issues: https://github.com/StuartMacKay/django-describe/issues
* Repository: https://github.com/StuartMacKay/django-describe/issues

The app is tested on Python 3.12+, and officially supports Django 5.2 LTS,
and later versions.

## License

django-describe is released under the terms of the [MIT](https://opensource.org/licenses/MIT) license.
